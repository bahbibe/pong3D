from django.contrib.auth.models import User
from django.test import TestCase, TransactionTestCase

from apps.accounts.models import Profile


class UniqueIntraIdMigrationTests(TransactionTestCase):
    def test_migration_clears_duplicates_before_adding_the_index(self):
        from django.db import connection
        from django.db.migrations.executor import MigrationExecutor

        before = [("api", "0015_backfill_missing_profiles")]
        executor = MigrationExecutor(connection)
        # Forward to the latest state (not just 0016), so later tests and the
        # current models find every column.
        after = executor.loader.graph.leaf_nodes()
        executor.migrate(before)
        old_apps = executor.loader.project_state(before).apps
        OldUser = old_apps.get_model("auth", "User")
        OldProfile = old_apps.get_model("api", "Profile")
        ids = []
        for name in ("dup_a", "dup_b"):
            user = OldUser.objects.create(username=name)
            ids.append(OldProfile.objects.create(user=user, intra_id=55, auth_method="intra").id)

        executor = MigrationExecutor(connection)
        executor.migrate(after)

        self.assertEqual(Profile.objects.get(id=ids[0]).intra_id, 55)
        self.assertIsNone(Profile.objects.get(id=ids[1]).intra_id)


class UniqueEmailMigrationTests(TransactionTestCase):
    def test_migration_keeps_email_on_oldest_account(self):
        from django.db import connection
        from django.db.migrations.executor import MigrationExecutor

        before = [("api", "0017_token_version_tfa_last_counter")]
        executor = MigrationExecutor(connection)
        after = executor.loader.graph.leaf_nodes()
        executor.migrate(before)
        OldUser = executor.loader.project_state(before).apps.get_model("auth", "User")
        oldest = OldUser.objects.create(username="d1", email="dup@example.com")
        newer = OldUser.objects.create(username="d2", email="DUP@example.com")
        other = OldUser.objects.create(username="d3", email="solo@example.com")

        executor = MigrationExecutor(connection)
        executor.migrate(after)

        emails = dict(User.objects.filter(id__in=[oldest.id, newer.id, other.id])
                      .values_list("username", "email"))
        self.assertEqual(emails, {"d1": "dup@example.com", "d2": "", "d3": "solo@example.com"})

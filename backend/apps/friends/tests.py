import json
from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.test import TestCase, TransactionTestCase

from apps.accounts.auth_utils import generate_token
from apps.accounts.models import Profile

from .models import Friendship


def make_user(username):
    user = User.objects.create_user(username=username, password="x-Strong-Pass-1")
    # Profile comes from the post_save signal.
    Profile.objects.filter(user=user).update(is_setup=True)
    user.refresh_from_db()
    return user


class FriendshipRuleTests(TestCase):
    def setUp(self):
        self.alice = make_user("alice")
        self.bob = make_user("bob")

    def as_user(self, user):
        self.client.cookies["access_token"] = generate_token(
            {"id": user.id, "is_tfa_verified": True, "exp": datetime.now() + timedelta(hours=1)}
        )

    def post(self, url, data):
        return self.client.post(url, data=json.dumps(data), content_type="application/json")

    def status_of(self):
        return Friendship.objects.get(source_user=self.alice, target_user=self.bob).status

    def test_accept_pending_request(self):
        Friendship.objects.create(source_user=self.alice, target_user=self.bob)
        self.as_user(self.bob)
        response = self.post("/api/friends/accept/", {"source_user": self.alice.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.status_of(), Friendship.ACCEPTED)

    def test_blocked_user_cannot_accept_old_request_to_undo_block(self):
        # Alice sent a request, then blocked Bob. Bob "accepting" used to
        # turn the block into a friendship.
        Friendship.objects.create(
            source_user=self.alice,
            target_user=self.bob,
            status=Friendship.BLOCKED,
            blocked_by=self.alice,
        )
        self.as_user(self.bob)
        response = self.post("/api/friends/accept/", {"source_user": self.alice.id})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.status_of(), Friendship.BLOCKED)

    def test_sender_cannot_accept_own_request(self):
        Friendship.objects.create(source_user=self.alice, target_user=self.bob)
        self.as_user(self.alice)
        response = self.post("/api/friends/accept/", {"source_user": self.bob.id})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.status_of(), Friendship.PENDING)

    def test_update_endpoint_is_gone(self):
        Friendship.objects.create(
            source_user=self.alice,
            target_user=self.bob,
            status=Friendship.BLOCKED,
            blocked_by=self.alice,
        )
        self.as_user(self.bob)
        response = self.client.put(
            "/api/friends/update/",
            data=json.dumps({"friend_id": self.alice.id, "status": "accepted"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.status_of(), Friendship.BLOCKED)

    def test_only_blocker_can_unblock(self):
        Friendship.objects.create(
            source_user=self.alice,
            target_user=self.bob,
            status=Friendship.BLOCKED,
            blocked_by=self.alice,
        )
        self.as_user(self.bob)
        response = self.post("/api/friends/unblock/", {"user_id": self.alice.id})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.status_of(), Friendship.BLOCKED)


class FriendshipPairTests(TestCase):
    def setUp(self):
        self.alice = make_user("alice")
        self.bob = make_user("bob")

    def as_user(self, user):
        self.client.cookies["access_token"] = generate_token(
            {"id": user.id, "is_tfa_verified": True, "exp": datetime.now() + timedelta(hours=1)}
        )

    def post(self, url, data):
        return self.client.post(url, data=json.dumps(data), content_type="application/json")

    def test_database_refuses_reverse_row(self):
        from django.db import IntegrityError, transaction

        Friendship.objects.create(source_user=self.alice, target_user=self.bob)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Friendship.objects.create(source_user=self.bob, target_user=self.alice)

    def test_crossed_requests_make_one_row(self):
        # Bob's request lands between Alice's "does a row exist?" check and
        # her insert. Simulate that window by hiding the existing row from
        # the check.
        from unittest import mock
        from django.db.models.query import QuerySet

        Friendship.objects.create(source_user=self.bob, target_user=self.alice)
        self.as_user(self.alice)
        with mock.patch.object(QuerySet, "exists", return_value=False):
            response = self.post("/api/friends/send/", {"target_user": self.bob.id})
        self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(Friendship.objects.count(), 1)

    def test_block_during_crossed_insert_blocks_existing_row(self):
        from unittest import mock
        from django.db.models.query import QuerySet

        Friendship.objects.create(source_user=self.bob, target_user=self.alice)
        self.as_user(self.alice)
        real_first = QuerySet.first
        calls = {"n": 0}

        def first_misses_friendship_once(qs):
            # Hide the row from the first Friendship lookup only.
            if qs.model is Friendship and calls["n"] == 0:
                calls["n"] += 1
                return None
            return real_first(qs)

        with mock.patch.object(QuerySet, "first", first_misses_friendship_once):
            response = self.post("/api/friends/block/", {"user_id": self.bob.id})
        self.assertEqual(response.status_code, 200, response.content)
        row = Friendship.objects.get()
        self.assertEqual((row.status, row.blocked_by_id), (Friendship.BLOCKED, self.alice.id))


class FriendshipPairMigrationTests(TransactionTestCase):
    def test_migration_keeps_one_row_per_pair(self):
        from django.db import connection
        from django.db.migrations.executor import MigrationExecutor

        before = [("friends", "0001_initial")]
        executor = MigrationExecutor(connection)
        after = executor.loader.graph.leaf_nodes()
        executor.migrate(before)
        old_apps = executor.loader.project_state(before).apps
        OldUser = old_apps.get_model("auth", "User")
        OldFriendship = old_apps.get_model("friends", "Friendship")
        a = OldUser.objects.create(username="pair_a")
        b = OldUser.objects.create(username="pair_b")
        c = OldUser.objects.create(username="pair_c")
        OldFriendship.objects.create(source_user=a, target_user=b, status="pending")
        blocked = OldFriendship.objects.create(
            source_user=b, target_user=a, status="blocked", blocked_by=b
        )
        single = OldFriendship.objects.create(source_user=a, target_user=c, status="accepted")

        executor = MigrationExecutor(connection)
        executor.migrate(after)

        self.assertEqual(
            sorted(Friendship.objects.values_list("id", flat=True)),
            sorted([blocked.id, single.id]),
        )

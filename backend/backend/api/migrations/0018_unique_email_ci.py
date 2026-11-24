from django.db import migrations

INDEX = "auth_user_email_ci_unique"


def blank_duplicate_emails(apps, schema_editor):
    """
    Before the index: for each email used by several accounts (any case),
    keep it on the oldest account and clear it on the others. Those users
    can still log in with their username.
    """
    User = apps.get_model("auth", "User")
    seen = set()
    for user in User.objects.exclude(email="").order_by("id").only("id", "email"):
        key = user.email.lower()
        if key in seen:
            User.objects.filter(id=user.id).update(email="")
        else:
            seen.add(key)


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0017_token_version_tfa_last_counter"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(blank_duplicate_emails, migrations.RunPython.noop),
        # auth.User is not our model, so the constraint is raw SQL. Empty
        # emails (intra accounts whose 42 email was taken) are allowed many times.
        migrations.RunSQL(
            f"CREATE UNIQUE INDEX {INDEX} ON auth_user (lower(email)) WHERE email <> ''",
            f"DROP INDEX IF EXISTS {INDEX}",
        ),
    ]

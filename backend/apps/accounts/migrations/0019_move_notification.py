# Notification moved to the notifications app (its 0001_initial). State
# only: the api_notification table is kept as it is.

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0018_unique_email_ci"),
        ("notifications", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[migrations.DeleteModel(name="Notification")],
            database_operations=[],
        ),
    ]

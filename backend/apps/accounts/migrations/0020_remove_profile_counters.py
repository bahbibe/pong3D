"""profile.total_wins and total_losses were never updated (stats come from
the games). They leave the model; the columns stay for one release.

The previous release still inserts these columns, so they get a database
default first: this release inserts profiles without them.
Next release: drop the two columns (RemoveField as a database operation).
"""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0019_move_notification"),
    ]

    operations = [
        migrations.AlterField(
            model_name="profile",
            name="total_wins",
            field=models.IntegerField(default=0, db_default=0),
        ),
        migrations.AlterField(
            model_name="profile",
            name="total_losses",
            field=models.IntegerField(default=0, db_default=0),
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveField(model_name="profile", name="total_wins"),
                migrations.RemoveField(model_name="profile", name="total_losses"),
            ],
        ),
    ]

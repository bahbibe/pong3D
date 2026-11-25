"""unique_together (source_user, target_user) only covered one direction;
friendship_unique_pair (0002) covers both, so the first one goes."""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("friends", "0002_unique_pair"),
    ]

    operations = [
        migrations.AlterUniqueTogether(name="friendship", unique_together=set()),
    ]

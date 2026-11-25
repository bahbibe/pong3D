"""Tournament_Game becomes TournamentGame; its table keeps its name, so the
previous release still works against it (rollback). unique_together on it
becomes a named UniqueConstraint (same rule).

Tournament_Participants is dropped with its table: no code ever used it,
in this release or the previous one, so a rollback does not need it.
"""

import django.db.models.deletion
from django.db import migrations, models


def _move_content_type(apps, old, new):
    ContentType = apps.get_model("contenttypes", "ContentType")
    rows = ContentType.objects.filter(app_label="game")
    if rows.filter(model=new).exists():
        # Both exist (e.g. a rolled-back release re-created the old one):
        # the old row is stale.
        rows.filter(model=old).delete()
    else:
        rows.filter(model=old).update(model=new)


def rename_content_type(apps, schema_editor):
    _move_content_type(apps, "tournament_game", "tournamentgame")


def restore_content_type(apps, schema_editor):
    _move_content_type(apps, "tournamentgame", "tournament_game")


class Migration(migrations.Migration):
    dependencies = [
        ("game", "0010_game_status_and_safe_foreign_keys"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.DeleteModel(name="Tournament_Participants"),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RenameModel(old_name="Tournament_Game", new_name="TournamentGame"),
                migrations.AlterModelTable(name="tournamentgame", table="game_tournament_game"),
                migrations.AlterField(
                    model_name="tournamentgame",
                    name="tournament",
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tournament_games",
                        to="game.tournament",
                    ),
                ),
                migrations.AlterField(
                    model_name="tournamentgame",
                    name="game",
                    field=models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tournament_games",
                        to="game.game",
                    ),
                ),
            ],
        ),
        migrations.AlterUniqueTogether(name="tournamentgame", unique_together=set()),
        migrations.AddConstraint(
            model_name="tournamentgame",
            constraint=models.UniqueConstraint(
                fields=("tournament", "game"), name="tournament_game_unique"
            ),
        ),
        migrations.RunPython(rename_content_type, restore_content_type),
    ]

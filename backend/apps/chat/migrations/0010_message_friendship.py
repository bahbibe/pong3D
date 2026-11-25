"""Messages point to their friendship with a foreign key instead of only
its uuid as text (conversation). The text column stays and is still
written, because the previous release reads it (rollback).

Next release: fill friendship again for rows a rolled-back release may
have written, make it non-null and drop conversation.
"""

import django.db.models.deletion
from django.db import migrations, models
from django.db.models import CharField, OuterRef, Subquery
from django.db.models.functions import Cast


def fill_friendship(apps, schema_editor):
    Friendship = apps.get_model("friends", "Friendship")
    Message = apps.get_model("chat", "Message")
    same_uuid = Friendship.objects.annotate(
        uuid_text=Cast("uuid", output_field=CharField())
    ).filter(uuid_text=OuterRef("conversation"))
    Message.objects.filter(friendship__isnull=True, conversation__isnull=False).update(
        friendship=Subquery(same_uuid.values("id")[:1])
    )


class Migration(migrations.Migration):
    dependencies = [
        ("chat", "0009_message_conversation_index"),
        ("friends", "0003_drop_directional_unique"),
    ]

    operations = [
        migrations.AddField(
            model_name="message",
            name="friendship",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="messages",
                to="friends.friendship",
            ),
        ),
        migrations.RunPython(fill_friendship, migrations.RunPython.noop),
    ]

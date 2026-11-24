# Moves Notification from the "api" app (apps/accounts) to this app.
# State only: the table (api_notification) and its rows stay as they are.

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def move_content_type(apps, schema_editor):
    # Keeps the content type id, so permissions pointing at it stay valid.
    ContentType = apps.get_model("contenttypes", "ContentType")
    ContentType.objects.filter(app_label="api", model="notification").update(
        app_label="notifications"
    )


def move_content_type_back(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    ContentType.objects.filter(app_label="notifications", model="notification").update(
        app_label="api"
    )


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("api", "0018_unique_email_ci"),
        ("contenttypes", "0002_remove_content_type_name"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="Notification",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("uuid", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                        ("type", models.CharField(max_length=255)),
                        ("message", models.TextField()),
                        ("is_read", models.BooleanField(default=False)),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("game_id", models.CharField(null=True)),
                        ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to=settings.AUTH_USER_MODEL)),
                        ("sender", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="sent_notifications", to=settings.AUTH_USER_MODEL)),
                    ],
                    options={"db_table": "api_notification"},
                ),
            ],
            database_operations=[],
        ),
        migrations.RunPython(move_content_type, move_content_type_back),
    ]

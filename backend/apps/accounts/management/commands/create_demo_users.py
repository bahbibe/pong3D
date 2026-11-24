"""Dev only: create a few accounts to play with.

    docker compose exec backend python manage.py create_demo_users [--count 4]

Users demo1..demoN, all with the same password, profile already set up.
Existing users are left alone, so it can run again. Refuses to run when
DJANGO_ALLOWED_HOSTS has a public name (a real server).
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import Profile

DEFAULT_PASSWORD = "Pong-Demo-Pass-42"
LOCAL_HOSTS = {"localhost", "127.0.0.1", "[::1]", "backend"}


class Command(BaseCommand):
    help = "Dev only: create demo users demo1..demoN."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=4)
        parser.add_argument("--password", default=DEFAULT_PASSWORD)

    def handle(self, *args, count, password, **options):
        public = [h for h in settings.ALLOWED_HOSTS if h not in LOCAL_HOSTS]
        if public:
            raise CommandError(
                f"Refusing to create demo users on a public site ({', '.join(public)})."
            )
        if count < 1:
            raise CommandError("--count must be at least 1.")

        User = get_user_model()
        created = 0
        for i in range(1, count + 1):
            username = f"demo{i}"
            if User.objects.filter(username=username).exists():
                continue
            user = User.objects.create_user(
                username=username,
                email=f"{username}@example.com",
                password=password,
                first_name="Demo",
                last_name=f"User{i}",
            )
            # The Profile comes from the post_save signal.
            Profile.objects.filter(user=user).update(is_setup=True)
            created += 1

        self.stdout.write(
            f"Created {created} demo user(s) (demo1..demo{count}), password: {password}"
        )

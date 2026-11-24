from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile

User = get_user_model()


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, raw=False, **kwargs):
    """
    Every user gets a Profile, however it was created (register, intra,
    admin, createsuperuser). Most of the code reads user.profile directly.
    """
    if created and not raw:
        Profile.objects.get_or_create(user=instance)

import factory

from chat.models import Message
from api.models import Profile
from friends.models import Friend
from faker import Faker

class ProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Profile

    uuid = factory.Faker("uuid4")
    avatar = factory.django.ImageField()
    auth_method = "email"
    is_setup = False
    total_wins = 0
    total_losses = 0
    user = factory.SubFactory("api.factories.UserFactory")
    is_tfa_enabled = False
    tfa_secret = factory.Faker("password")

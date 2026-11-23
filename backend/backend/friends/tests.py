import json
from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.test import TestCase

from api.auth_utils import generate_token
from api.models import Profile

from .models import Friendship


def make_user(username):
    user = User.objects.create_user(username=username, password="x-Strong-Pass-1")
    # Profile comes from the post_save signal.
    Profile.objects.filter(user=user).update(is_setup=True)
    user.refresh_from_db()
    return user


class FriendshipRuleTests(TestCase):
    def setUp(self):
        self.alice = make_user("alice")
        self.bob = make_user("bob")

    def as_user(self, user):
        self.client.cookies["access_token"] = generate_token(
            {"id": user.id, "is_tfa_verified": True, "exp": datetime.now() + timedelta(hours=1)}
        )

    def post(self, url, data):
        return self.client.post(url, data=json.dumps(data), content_type="application/json")

    def status_of(self):
        return Friendship.objects.get(source_user=self.alice, target_user=self.bob).status

    def test_accept_pending_request(self):
        Friendship.objects.create(source_user=self.alice, target_user=self.bob)
        self.as_user(self.bob)
        response = self.post("/api/friends/accept/", {"source_user": self.alice.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.status_of(), Friendship.ACCEPTED)

    def test_blocked_user_cannot_accept_old_request_to_undo_block(self):
        # Alice sent a request, then blocked Bob. Bob "accepting" used to
        # turn the block into a friendship.
        Friendship.objects.create(
            source_user=self.alice,
            target_user=self.bob,
            status=Friendship.BLOCKED,
            blocked_by=self.alice,
        )
        self.as_user(self.bob)
        response = self.post("/api/friends/accept/", {"source_user": self.alice.id})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.status_of(), Friendship.BLOCKED)

    def test_sender_cannot_accept_own_request(self):
        Friendship.objects.create(source_user=self.alice, target_user=self.bob)
        self.as_user(self.alice)
        response = self.post("/api/friends/accept/", {"source_user": self.bob.id})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.status_of(), Friendship.PENDING)

    def test_update_endpoint_is_gone(self):
        Friendship.objects.create(
            source_user=self.alice,
            target_user=self.bob,
            status=Friendship.BLOCKED,
            blocked_by=self.alice,
        )
        self.as_user(self.bob)
        response = self.client.put(
            "/api/friends/update/",
            data=json.dumps({"friend_id": self.alice.id, "status": "accepted"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.status_of(), Friendship.BLOCKED)

    def test_only_blocker_can_unblock(self):
        Friendship.objects.create(
            source_user=self.alice,
            target_user=self.bob,
            status=Friendship.BLOCKED,
            blocked_by=self.alice,
        )
        self.as_user(self.bob)
        response = self.post("/api/friends/unblock/", {"user_id": self.alice.id})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.status_of(), Friendship.BLOCKED)

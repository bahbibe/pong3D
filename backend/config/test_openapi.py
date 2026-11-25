"""Real responses match the OpenAPI schema (docs/openapi.yaml comes from the
same generator), so the documentation cannot drift from the code."""

import copy
from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from drf_spectacular.generators import SchemaGenerator
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from apps.accounts.auth_utils import generate_token
from apps.accounts.models import Profile
from apps.friends.models import Friendship
from apps.game.models import Game

SCHEMA = SchemaGenerator().get_schema(request=None, public=True)


def _as_json_schema(node):
    """OpenAPI 3.0 marks null with nullable: true; JSON Schema needs it in the type."""
    if isinstance(node, list):
        return [_as_json_schema(item) for item in node]
    if not isinstance(node, dict):
        return node
    node = {key: _as_json_schema(value) for key, value in node.items()}
    if node.pop("nullable", False):
        if "type" in node:
            node["type"] = [node["type"], "null"]
        else:
            node = {"anyOf": [node, {"type": "null"}]}
    return node


DOCUMENT = _as_json_schema(copy.deepcopy(SCHEMA))
REGISTRY = Registry().with_resource(
    "urn:api", Resource.from_contents(DOCUMENT, default_specification=DRAFT202012)
)


def response_schema(path, method, status):
    operation = DOCUMENT["paths"][path][method]
    schema = operation["responses"][str(status)]["content"]["application/json"]["schema"]
    if "$ref" in schema:
        schema = {"$ref": "urn:api" + schema["$ref"]}
    return schema


def _rebase(node):
    """Make #/components refs absolute (urn:api#/components/...)."""
    if isinstance(node, list):
        return [_rebase(item) for item in node]
    if isinstance(node, dict):
        return {
            key: ("urn:api" + value if key == "$ref" and value.startswith("#") else _rebase(value))
            for key, value in node.items()
        }
    return node


def token_for(user):
    return generate_token(
        {
            "id": user.id,
            "is_tfa_verified": True,
            "ver": 0,
            "exp": datetime.now() + timedelta(hours=1),
        }
    )


def make_user(name):
    user = User.objects.create_user(username=name, email=f"{name}@x.io", password="x-Strong-Pass-1")
    Profile.objects.filter(user=user).update(is_setup=True)
    return user


class ResponsesMatchTheSchemaTests(TestCase):
    def setUp(self):
        self.alice, self.bob = make_user("alice"), make_user("bob")
        self.friendship = Friendship.objects.create(
            source_user=self.alice, target_user=self.bob, status=Friendship.ACCEPTED
        )
        self.game = Game.objects.create(
            player1=self.alice,
            player2=self.bob,
            player1_score=11,
            player2_score=3,
            status=Game.FINISHED,
            winner=self.alice,
        )
        self.client.cookies["access_token"] = token_for(self.alice)

    def check(self, method, url, path, status=200, **kwargs):
        response = getattr(self.client, method)(url, content_type="application/json", **kwargs)
        self.assertEqual(response.status_code, status, response.content)
        validator = Draft202012Validator(
            _rebase(response_schema(path, method, status)), registry=REGISTRY
        )
        errors = sorted(validator.iter_errors(response.json()), key=str)
        self.assertEqual([f"{list(e.path)}: {e.message}" for e in errors], [], url)

    def test_auth_and_profile(self):
        self.check("get", "/api/auth/me/", "/api/auth/me/")
        self.check("get", "/api/auth/users/?q=bo", "/api/auth/users/")
        uuid = Profile.objects.get(user=self.bob).uuid
        self.check("get", f"/api/auth/profile/{uuid}/", "/api/auth/profile/{uuid}/")
        self.client.cookies.clear()
        self.check(
            "post",
            "/api/auth/login/",
            "/api/auth/login/",
            data={"username": "alice", "password": "x-Strong-Pass-1"},
        )

    def test_games(self):
        self.check("get", "/api/game/leaderboard/?size=1", "/api/game/leaderboard/")
        self.check("get", "/api/game/history/", "/api/game/history/")
        self.check("get", "/api/game/stats/", "/api/game/stats/")
        self.check("get", f"/api/game/get_game/{self.game.id}", "/api/game/get_game/{game_id}")
        self.check(
            "post", f"/api/game/invite_friend/{self.bob.id}", "/api/game/invite_friend/{friend_id}"
        )
        self.check("post", "/api/game/create_tournament/", "/api/game/create_tournament/")
        self.check("get", "/api/game/get_tournaments/", "/api/game/get_tournaments/")

    def test_friends_chat_notifications(self):
        self.check("get", "/api/friends/", "/api/friends/")
        self.check("get", "/api/friends/blocked/", "/api/friends/blocked/")
        self.check(
            "get",
            f"/api/chat/messages/{self.friendship.uuid}/",
            "/api/chat/messages/{conversation}/",
        )
        self.check(
            "post", "/api/auth/notifications/mark_as_read/", "/api/auth/notifications/mark_as_read/"
        )

    def test_errors_have_the_error_shape(self):
        self.check(
            "post",
            "/api/friends/send/",
            "/api/friends/send/",
            status=400,
            data={"target_user": "not-a-user"},
        )
        self.check(
            "get", "/api/chat/messages/not-a-uuid/", "/api/chat/messages/{conversation}/", 404
        )

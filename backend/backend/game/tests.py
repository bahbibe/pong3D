import asyncio
import json
from datetime import datetime, timedelta
from unittest import mock

from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import User
from django.test import TransactionTestCase

from api.auth_utils import generate_token
from api.models import Profile
from ft_transcendence.asgi import application

from . import game_manager as gm
from .consumers import bot_manager, game_manager
from .models import Game


def make_user(username):
    user = User.objects.create_user(username=username, password="x-Strong-Pass-1")
    # Profile comes from the post_save signal.
    Profile.objects.filter(user=user).update(is_setup=True)
    user.refresh_from_db()
    return user


def token_for(user):
    return generate_token(
        {"id": user.id, "is_tfa_verified": True, "exp": datetime.now() + timedelta(hours=1)}
    )


async def ws_connect(path, user=None):
    headers = [(b"origin", b"http://localhost")]
    if user is not None:
        headers.append((b"cookie", f"access_token={token_for(user)}".encode()))
    communicator = WebsocketCommunicator(application, path, headers=headers)
    connected, _ = await communicator.connect()
    assert connected
    return communicator


async def receive_until(communicator, message_type, timeout=5):
    """Read messages until one with `type` == message_type arrives."""
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while True:
        remaining = deadline - loop.time()
        if remaining <= 0:
            raise AssertionError(f"no {message_type!r} message within {timeout}s")
        message = json.loads(await communicator.receive_from(timeout=remaining))
        if message.get("type") == message_type:
            return message


async def wait_for(predicate, timeout=3):
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while not predicate():
        if loop.time() > deadline:
            raise AssertionError("condition not met in time")
        await asyncio.sleep(0.05)


class GameTestCase(TransactionTestCase):
    def setUp(self):
        self.alice = make_user("alice")
        self.bob = make_user("bob")
        self.eve = make_user("eve")
        self.game = Game.objects.create(player1=self.alice, player2=self.bob)
        self.path = f"/ws/game/{self.game.id}"

    def tearDown(self):
        game_manager.stop_all()
        bot_manager.stop_all()


class GameConsumerAccessTests(GameTestCase):
    async def assert_closed_with(self, communicator, code):
        output = await communicator.receive_output(timeout=2)
        self.assertEqual(output["type"], "websocket.close")
        self.assertEqual(output.get("code"), code)

    async def test_anonymous_is_rejected(self):
        communicator = await ws_connect(self.path)
        await self.assert_closed_with(communicator, 4001)
        self.assertEqual(game_manager.game_instances, {})

    async def test_non_player_is_rejected(self):
        communicator = await ws_connect(self.path, self.eve)
        await self.assert_closed_with(communicator, 4003)
        self.assertEqual(game_manager.game_instances, {})

    async def test_unknown_game_is_rejected(self):
        communicator = await ws_connect("/ws/game/999999", self.alice)
        await self.assert_closed_with(communicator, 4003)

    async def test_finished_game_does_not_restart(self):
        await database_sync_to_async(
            Game.objects.filter(pk=self.game.pk).update
        )(player1_score=11, player2_score=4)
        communicator = await ws_connect(self.path, self.alice)
        message = json.loads(await communicator.receive_from(timeout=2))
        self.assertEqual(message["type"], "game over")
        output = await communicator.receive_output(timeout=2)
        self.assertEqual(output["type"], "websocket.close")
        self.assertEqual(game_manager.game_instances, {})


class GameLoopTests(GameTestCase):
    async def test_remote_game_sends_state_updates(self):
        # Regression: the loop used self.player (bot-only attribute) and
        # crashed on its first tick, so players never got any state.
        alice = await ws_connect(self.path, self.alice)
        bob = await ws_connect(self.path, self.bob)
        message = await receive_until(alice, "game_update_message")
        self.assertEqual(message["game_state"]["side"], "player1")
        message = await receive_until(bob, "game_update_message")
        self.assertEqual(message["game_state"]["side"], "player2")
        instance = game_manager.game_instances[str(self.game.id)]
        self.assertFalse(instance.game_loop_task.done())
        await alice.disconnect()
        await bob.disconnect()

    async def test_spamming_moves_does_not_move_paddle(self):
        alice = await ws_connect(self.path, self.alice)
        instance = game_manager.game_instances[str(self.game.id)]
        for _ in range(200):
            await alice.send_to(text_data=json.dumps({"type": "move", "direction": "left"}))
        await wait_for(lambda: instance.directions["player1"] == 1)
        # Bob never joined, so no tick has run: messages only set direction.
        self.assertEqual(instance.game_state["player1"], 0)
        await alice.disconnect()

    async def test_old_and_bad_messages_are_ignored(self):
        alice = await ws_connect(self.path, self.alice)
        instance = game_manager.game_instances[str(self.game.id)]
        for payload in [
            json.dumps({"type": "left"}),
            json.dumps({"type": "game_update", "ball_position": [0, 0]}),
            json.dumps({"type": "move", "direction": "up"}),
            json.dumps(["move"]),
            "not json",
        ]:
            await alice.send_to(text_data=payload)
        self.assertTrue(await alice.receive_nothing(timeout=0.3) or True)
        self.assertEqual(instance.directions, {"player1": 0, "player2": 0})
        self.assertFalse(instance.game_loop_task.done())
        await alice.disconnect()

    async def test_player2_direction_is_flipped(self):
        bob = await ws_connect(self.path, self.bob)
        instance = game_manager.game_instances[str(self.game.id)]
        await bob.send_to(text_data=json.dumps({"type": "move", "direction": "left"}))
        await wait_for(lambda: instance.directions["player2"] == -1)
        await bob.disconnect()

    async def test_abandoned_game_loop_stops(self):
        with mock.patch.object(gm, "ABANDON_TIMEOUT_SECONDS", 0.2):
            alice = await ws_connect(self.path, self.alice)
            instance = game_manager.game_instances[str(self.game.id)]
            await alice.disconnect()
            await wait_for(instance.game_loop_task.done, timeout=4)
        self.assertNotIn(str(self.game.id), game_manager.game_instances)


class GameInstanceUnitTests(GameTestCase):
    async def test_paddle_moves_one_step_per_tick_and_is_clamped(self):
        instance = gm.GameInstance(self.game, mock.AsyncMock())
        instance.stop()
        instance.set_direction("player1", 1)
        instance.apply_paddle_moves()
        self.assertAlmostEqual(instance.game_state["player1"], gm.PADDLE_STEP)
        for _ in range(1000):
            instance.apply_paddle_moves()
        self.assertEqual(instance.game_state["player1"], gm.PADDLE_LIMIT)

    async def test_score_save_does_not_overwrite_players(self):
        instance = gm.GameInstance(self.game, mock.AsyncMock())
        instance.stop()
        # Someone else changes the players of this row after it was loaded.
        await database_sync_to_async(
            Game.objects.filter(pk=self.game.pk).update
        )(player2=self.eve)
        instance.game_state["ball_position"] = [0, -4.95]
        instance.vel = [1, -1]
        self.assertTrue(instance.update_ball_position())
        await instance.save_scores()
        game = await database_sync_to_async(Game.objects.get)(pk=self.game.pk)
        self.assertEqual(game.player1_score, 1)
        self.assertEqual(game.player2_id, self.eve.id)

    async def test_no_save_without_score(self):
        instance = gm.GameInstance(self.game, mock.AsyncMock())
        instance.stop()
        self.assertFalse(instance.update_ball_position())


class BotConsumerTests(GameTestCase):
    async def test_anonymous_is_rejected(self):
        communicator = await ws_connect("/ws/game/bot")
        output = await communicator.receive_output(timeout=2)
        self.assertEqual(output.get("code"), 4001)
        self.assertEqual(bot_manager.bot_instances, {})

    async def test_disconnect_stops_bot_loop(self):
        communicator = await ws_connect("/ws/game/bot", self.alice)
        await receive_until(communicator, "game_update_message")
        instance = bot_manager.bot_instances[str(self.alice.id)]
        self.assertEqual(instance.group_name, f"bot_{self.alice.id}")
        await communicator.disconnect()
        await wait_for(instance.game_loop_task.done)
        self.assertEqual(bot_manager.bot_instances, {})

    async def test_new_tab_replaces_old_bot_game(self):
        first = await ws_connect("/ws/game/bot", self.alice)
        old = bot_manager.bot_instances[str(self.alice.id)]
        second = await ws_connect("/ws/game/bot", self.alice)
        new = bot_manager.bot_instances[str(self.alice.id)]
        self.assertIsNot(old, new)
        await wait_for(old.game_loop_task.done)
        # Closing the old tab must not stop the new game.
        await first.disconnect()
        await asyncio.sleep(0.1)
        self.assertFalse(new.game_loop_task.done())
        await second.disconnect()
        await wait_for(new.game_loop_task.done)

    async def test_bot_move_message(self):
        communicator = await ws_connect("/ws/game/bot", self.alice)
        instance = bot_manager.bot_instances[str(self.alice.id)]
        await communicator.send_to(text_data=json.dumps({"type": "move", "direction": "right"}))
        await wait_for(lambda: instance.directions["player1"] == -1)
        await communicator.disconnect()


class TournamentConsumerTests(GameTestCase):
    async def test_anonymous_is_rejected(self):
        communicator = await ws_connect(
            "/ws/tournament/12345678-1234-4123-8123-123456789012"
        )
        output = await communicator.receive_output(timeout=2)
        self.assertEqual(output.get("code"), 4001)

    async def test_unknown_tournament_closes_cleanly(self):
        communicator = await ws_connect(
            "/ws/tournament/12345678-1234-4123-8123-123456789012", self.alice
        )
        output = await communicator.receive_output(timeout=2)
        self.assertEqual(output.get("code"), 4004)


class GameActionViewTests(TransactionTestCase):
    def setUp(self):
        from friends.models import Friendship

        self.alice = make_user("alice")
        self.bob = make_user("bob")
        self.carol = make_user("carol")
        Friendship.objects.create(
            source_user=self.alice, target_user=self.bob, status=Friendship.ACCEPTED
        )
        Friendship.objects.create(
            source_user=self.alice, target_user=self.carol, status=Friendship.PENDING
        )
        self.client.cookies["access_token"] = token_for(self.alice)

    def test_state_changing_actions_reject_get(self):
        game = Game.objects.create(player1=self.alice, player2=self.bob)
        for url in [
            "/api/game/create_tournament/",
            f"/api/game/invite_friend/{self.bob.id}",
            f"/api/game/play_again/{game.id}",
        ]:
            self.assertEqual(self.client.get(url).status_code, 405, url)
        self.assertEqual(Game.objects.count(), 1)

    def test_invite_friend_with_post(self):
        response = self.client.post(f"/api/game/invite_friend/{self.bob.id}")
        self.assertEqual(response.status_code, 200, response.content)
        game = Game.objects.get(id=response.json()["data"]["game"]["id"])
        self.assertEqual((game.player1_id, game.player2_id), (self.alice.id, self.bob.id))

    def test_cannot_invite_non_friend(self):
        response = self.client.post(f"/api/game/invite_friend/{self.carol.id}")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Game.objects.count(), 0)

    def test_invite_unknown_user(self):
        response = self.client.post("/api/game/invite_friend/abc")
        self.assertEqual(response.status_code, 400)

    def test_create_tournament_post_path_used_by_frontend(self):
        # API.js must use the trailing slash: a POST to the slash-less URL
        # is redirected and comes back as a GET.
        api_js = (
            __import__("pathlib").Path(__file__).resolve().parents[3]
            / "frontend/static/js/API/API.js"
        )
        if api_js.exists():  # not present inside the backend container
            self.assertIn("/api/game/create_tournament/`", api_js.read_text())
        response = self.client.post("/api/game/create_tournament/")
        self.assertEqual(response.status_code, 200, response.content)


class GameStatusTests(TransactionTestCase):
    def setUp(self):
        self.alice = make_user("alice")
        self.bob = make_user("bob")

    def tearDown(self):
        game_manager.stop_all()

    async def test_finish_game_records_status_winner_and_time(self):
        game = await database_sync_to_async(Game.objects.create)(
            player1=self.alice, player2=self.bob, player1_score=11, player2_score=7
        )
        instance = gm.GameInstance(game, mock.AsyncMock())
        instance.stop()
        await instance.finish_game()
        game = await database_sync_to_async(Game.objects.get)(pk=game.pk)
        self.assertEqual(game.status, Game.FINISHED)
        self.assertEqual(game.winner_id, self.alice.id)
        self.assertIsNotNone(game.finished_at)

    async def test_mark_playing(self):
        game = await database_sync_to_async(Game.objects.create)(
            player1=self.alice, player2=self.bob
        )
        instance = gm.GameInstance(game, mock.AsyncMock())
        instance.stop()
        await instance.mark_playing()
        game = await database_sync_to_async(Game.objects.get)(pk=game.pk)
        self.assertEqual(game.status, Game.PLAYING)

    async def test_finished_status_blocks_restart_even_without_winning_score(self):
        game = await database_sync_to_async(Game.objects.create)(
            player1=self.alice, player2=self.bob, player1_score=3, status=Game.FINISHED
        )
        communicator = await ws_connect(f"/ws/game/{game.id}", self.alice)
        message = json.loads(await communicator.receive_from(timeout=2))
        self.assertEqual(message["type"], "game over")
        self.assertEqual(game_manager.game_instances, {})

    def test_stats_ignore_unplayed_games(self):
        # Regression: an unplayed invite (0-0) counted as a loss for both.
        Game.objects.create(player1=self.alice, player2=self.bob)  # pending invite
        Game.objects.create(
            player1=self.alice, player2=self.bob, player1_score=11, player2_score=5,
            status=Game.FINISHED, winner=self.alice,
        )
        self.client.cookies["access_token"] = token_for(self.bob)
        stats = self.client.get("/api/game/stats/").json()["data"]
        self.assertEqual(stats["total_games"], 1)
        self.assertEqual(stats["total_losses"], 1)
        history = self.client.get("/api/game/history/").json()["data"]
        self.assertEqual(len(history["games"]), 1)
        profile = self.client.get(f"/api/auth/profile/{self.alice.profile.uuid}/").json()
        self.assertEqual(profile["data"]["stats"]["total_wins"], 1)
        self.assertEqual(profile["data"]["stats"]["total_games"], 1)

    def test_data_migration_marks_old_finished_games(self):
        import importlib

        from django.apps import apps

        migration = importlib.import_module(
            "game.migrations.0010_game_status_and_safe_foreign_keys"
        )
        done = Game.objects.create(player1=self.alice, player2=self.bob, player1_score=4, player2_score=11)
        open_game = Game.objects.create(player1=self.alice, player2=self.bob, player1_score=4)
        migration.mark_finished_games(apps, None)
        done.refresh_from_db()
        open_game.refresh_from_db()
        self.assertEqual((done.status, done.winner_id), (Game.FINISHED, self.bob.id))
        self.assertEqual(open_game.status, Game.PENDING)


class DeleteUserTests(TransactionTestCase):
    def test_deleting_a_user_keeps_games_and_tournaments(self):
        from .models import Tournament, Tournament_Game

        alice, bob = make_user("alice"), make_user("bob")
        game = Game.objects.create(player1=alice, player2=bob, status=Game.FINISHED, winner=alice)
        tournament = Tournament.objects.create(owner=alice)
        Tournament_Game.objects.create(tournament=tournament, game=game, t_round=1)

        alice.delete()  # used to fail: DO_NOTHING foreign keys

        game.refresh_from_db()
        tournament.refresh_from_db()
        self.assertIsNone(game.player1_id)
        self.assertIsNone(game.winner_id)
        self.assertEqual(game.player2_id, bob.id)
        self.assertIsNone(tournament.owner_id)

        tournament.delete()
        self.assertFalse(Tournament_Game.objects.exists())


class LeaderboardTests(TransactionTestCase):
    def test_counts_finished_games_and_handles_intra_avatars(self):
        alice, bob = make_user("alice"), make_user("bob")
        Profile.objects.filter(user=bob).update(avatar="https://cdn.intra.42.fr/users/bob.jpg")
        Game.objects.create(player1=alice, player2=bob, player1_score=11, status=Game.FINISHED, winner=alice)
        Game.objects.create(player1=alice, player2=bob, player2_score=11, status=Game.FINISHED, winner=bob)
        Game.objects.create(player1=alice, player2=bob, player1_score=11, status=Game.FINISHED, winner=alice)
        Game.objects.create(player1=alice, player2=bob)  # pending, ignored
        self.client.cookies["access_token"] = token_for(alice)
        response = self.client.get("/api/game/leaderboard/")
        self.assertEqual(response.status_code, 200, response.content)
        rows = {row["user"]["username"]: row for row in response.json()["data"]["users"]}
        self.assertEqual((rows["alice"]["total_games"], rows["alice"]["total_wins"]), (3, 2))
        self.assertEqual((rows["bob"]["total_games"], rows["bob"]["total_wins"]), (3, 1))
        self.assertEqual(rows["bob"]["user"]["avatar"], "https://cdn.intra.42.fr/users/bob.jpg")
        self.assertNotIn("email", rows["alice"]["user"])

    def test_play_again_without_opponent(self):
        alice = make_user("alice")
        game = Game.objects.create(player1=alice, player2=None)
        self.client.cookies["access_token"] = token_for(alice)
        response = self.client.post(f"/api/game/play_again/{game.id}")
        self.assertEqual(response.status_code, 400)

    def test_unknown_tournament_games(self):
        alice = make_user("alice")
        self.client.cookies["access_token"] = token_for(alice)
        self.assertEqual(self.client.get("/api/game/get_tournament_games/nope").status_code, 404)


class TournamentBracketTests(TransactionTestCase):
    def setUp(self):
        from .models import Tournament

        self.players = [make_user(f"p{i}") for i in range(4)]
        self.tournament = Tournament.objects.create(owner=self.players[0])

    def entries(self, t_round):
        from .models import Tournament_Game

        return list(
            Tournament_Game.objects.filter(tournament=self.tournament, t_round=t_round)
            .select_related("game").order_by("id")
        )

    def test_bracket_is_created_once(self):
        from .tournament import ensure_bracket

        ensure_bracket(self.tournament)
        ensure_bracket(self.tournament)
        self.assertEqual((len(self.entries(2)), len(self.entries(1))), (2, 1))

    def test_create_tournament_view_builds_bracket(self):
        from .models import Tournament_Game

        self.client.cookies["access_token"] = token_for(self.players[1])
        response = self.client.post("/api/game/create_tournament/")
        uuid = response.json()["data"]["data"]["uuid"]
        self.assertEqual(Tournament_Game.objects.filter(tournament__uuid=uuid).count(), 3)

    def test_seats_fill_in_order_and_no_double_seat(self):
        from .tournament import ensure_bracket, take_seat

        ensure_bracket(self.tournament)
        for player in self.players:
            take_seat(self.tournament, player, 2)
        take_seat(self.tournament, self.players[0], 2)  # already seated
        seated = [
            (e.game.player1_id, e.game.player2_id) for e in self.entries(2)
        ]
        ids = [p.id for p in self.players]
        self.assertEqual(seated, [(ids[0], ids[1]), (ids[2], ids[3])])

    def test_leave_frees_seat_only_without_opponent(self):
        from .tournament import ensure_bracket, leave_seat, take_seat

        ensure_bracket(self.tournament)
        take_seat(self.tournament, self.players[0], 2)
        leave_seat(self.tournament, self.players[0], 2)
        self.assertIsNone(self.entries(2)[0].game.player1_id)

        take_seat(self.tournament, self.players[0], 2)
        take_seat(self.tournament, self.players[1], 2)
        leave_seat(self.tournament, self.players[0], 2)
        self.assertEqual(self.entries(2)[0].game.player1_id, self.players[0].id)

    async def test_winners_advance_and_final_finishes_tournament(self):
        # Regression: qualification ran in the winner's socket handler, so a
        # winner who had disconnected never reached the final.
        from .tournament import ensure_bracket, take_seat

        await database_sync_to_async(ensure_bracket)(self.tournament)
        for player in self.players:
            await database_sync_to_async(take_seat)(self.tournament, player, 2)
        first_round = await database_sync_to_async(self.entries)(2)

        async def play(game, p1_score, p2_score):
            game.player1_score, game.player2_score = p1_score, p2_score
            instance = gm.GameInstance(game, mock.AsyncMock())
            instance.stop()
            await instance.finish_game()

        await play(first_round[0].game, 11, 3)  # p0 wins
        await play(first_round[1].game, 2, 11)  # p3 wins
        final = (await database_sync_to_async(self.entries)(1))[0].game
        await database_sync_to_async(final.refresh_from_db)()
        self.assertEqual((final.player1_id, final.player2_id), (self.players[0].id, self.players[3].id))

        await play(final, 11, 9)
        await database_sync_to_async(self.tournament.refresh_from_db)()
        self.assertTrue(self.tournament.finished)

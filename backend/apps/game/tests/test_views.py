import json
from unittest import mock

from channels.db import database_sync_to_async
from django.test import TransactionTestCase

from apps.accounts.models import Profile
from apps.game import game_manager as gm
from apps.game.consumers import game_manager
from apps.game.models import Game

from .helpers import make_user, token_for, ws_connect


class GameActionViewTests(TransactionTestCase):
    def setUp(self):
        from apps.friends.models import Friendship

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
        # Inside the backend image there is no frontend, so only the
        # request is checked there.
        parents = __import__("pathlib").Path(__file__).resolve().parents
        candidates = [p / "frontend/static/js/API/API.js" for p in parents]
        api_js = next((c for c in candidates if c.exists()), None)
        if api_js is not None:
            self.assertRegex(api_js.read_text(), r"/api/game/create_tournament/[`\"']")
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
            player1=self.alice,
            player2=self.bob,
            player1_score=11,
            player2_score=5,
            status=Game.FINISHED,
            winner=self.alice,
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
            "apps.game.migrations.0010_game_status_and_safe_foreign_keys"
        )
        done = Game.objects.create(
            player1=self.alice, player2=self.bob, player1_score=4, player2_score=11
        )
        open_game = Game.objects.create(player1=self.alice, player2=self.bob, player1_score=4)
        migration.mark_finished_games(apps, None)
        done.refresh_from_db()
        open_game.refresh_from_db()
        self.assertEqual((done.status, done.winner_id), (Game.FINISHED, self.bob.id))
        self.assertEqual(open_game.status, Game.PENDING)


class DeleteUserTests(TransactionTestCase):
    def test_deleting_a_user_keeps_games_and_tournaments(self):
        from apps.game.models import Tournament, TournamentGame

        alice, bob = make_user("alice"), make_user("bob")
        game = Game.objects.create(player1=alice, player2=bob, status=Game.FINISHED, winner=alice)
        tournament = Tournament.objects.create(owner=alice)
        TournamentGame.objects.create(tournament=tournament, game=game, t_round=1)

        alice.delete()  # used to fail: DO_NOTHING foreign keys

        game.refresh_from_db()
        tournament.refresh_from_db()
        self.assertIsNone(game.player1_id)
        self.assertIsNone(game.winner_id)
        self.assertEqual(game.player2_id, bob.id)
        self.assertIsNone(tournament.owner_id)

        tournament.delete()
        self.assertFalse(TournamentGame.objects.exists())


class LeaderboardTests(TransactionTestCase):
    def test_counts_finished_games_and_handles_intra_avatars(self):
        alice, bob = make_user("alice"), make_user("bob")
        Profile.objects.filter(user=bob).update(avatar="https://cdn.intra.42.fr/users/bob.jpg")
        Game.objects.create(
            player1=alice, player2=bob, player1_score=11, status=Game.FINISHED, winner=alice
        )
        Game.objects.create(
            player1=alice, player2=bob, player2_score=11, status=Game.FINISHED, winner=bob
        )
        Game.objects.create(
            player1=alice, player2=bob, player1_score=11, status=Game.FINISHED, winner=alice
        )
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

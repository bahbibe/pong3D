from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.game import selectors, services
from apps.game.models import Game
from core.errors import NotFound, ServiceError

from .helpers import make_user


class StatsAndHistoryTests(TestCase):
    def setUp(self):
        self.alice = make_user("alice")
        self.bob = make_user("bob")

        def game(p1, p2, s1, s2, status=Game.FINISHED):
            return Game.objects.create(
                player1=p1, player2=p2, player1_score=s1, player2_score=s2, status=status
            )

        game(self.alice, self.bob, 5, 3)  # alice wins as player1
        game(self.bob, self.alice, 1, 5)  # alice wins as player2
        game(self.bob, self.alice, 5, 2)  # alice loses
        game(self.alice, self.bob, 4, 4)  # draw: not a win
        game(self.alice, self.bob, 9, 0, status=Game.PENDING)  # not finished: ignored

    def test_stats(self):
        self.assertEqual(
            selectors.stats(self.alice),
            {"total_games": 4, "total_wins": 2, "total_losses": 2, "ratio": 50.0},
        )
        self.assertEqual(selectors.stats(self.bob)["total_wins"], 1)

    def test_history_is_seen_from_the_user_side(self):
        rows = selectors.history(self.alice)
        self.assertEqual(len(rows), 4)
        newest = rows[0]  # the draw
        self.assertEqual((newest.user, newest.player), (self.alice, self.bob))
        self.assertFalse(newest.is_user_winner)
        as_player2 = rows[2]
        self.assertEqual((as_player2.user_score, as_player2.player_score), (5, 1))
        self.assertTrue(as_player2.is_user_winner)

    def test_history_endpoint_query_count_does_not_grow_with_games(self):
        from datetime import datetime, timedelta

        from apps.accounts.auth_utils import generate_token

        self.client.cookies["access_token"] = generate_token(
            {
                "id": self.alice.id,
                "is_tfa_verified": True,
                "exp": datetime.now() + timedelta(hours=1),
            }
        )
        with self.assertNumQueries(2):  # the user with its profile (auth), the games with players
            self.assertEqual(self.client.get("/api/game/history/").status_code, 200)

    def test_leaderboard_order(self):
        order, _, _ = selectors.leaderboard_order()
        users = {u.id: u.username for u in get_user_model().objects.all()}
        self.assertEqual([users[i] for i in order][:2], ["alice", "bob"])


class GameServiceTests(TestCase):
    def setUp(self):
        self.alice = make_user("alice")
        self.bob = make_user("bob")
        self.carol = make_user("carol")

    def test_get_game_and_tournament_errors(self):
        for bad in ("abc", "999999", "-1"):
            with self.assertRaisesMessage(ServiceError, "Game not found"):
                services.get_game(bad)
        for bad in ("not-a-uuid", "00000000-0000-0000-0000-000000000000"):
            with self.assertRaises(NotFound):
                services.get_tournament(bad)

    def test_play_again_only_for_own_games(self):
        game = Game.objects.create(player1=self.alice, player2=self.bob, status=Game.FINISHED)
        with self.assertRaisesMessage(ServiceError, services.COULD_NOT_CREATE):
            services.play_again(self.carol, game.id)
        new = services.play_again(self.bob, game.id)
        self.assertEqual((new.player1, new.player2), (self.bob, self.alice))

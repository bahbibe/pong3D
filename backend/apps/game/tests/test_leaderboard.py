from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from apps.friends.models import Friendship
from apps.game.models import Game

from .helpers import make_user, token_for


def finished(winner, loser):
    return Game.objects.create(
        player1=winner,
        player2=loser,
        player1_score=5,
        player2_score=1,
        status=Game.FINISHED,
        winner=winner,
    )


class LeaderboardTests(TestCase):
    def setUp(self):
        # a: 2 wins of 2, b: 1 of 1 (same ratio, fewer wins), c: 1 of 3, d and e: no games.
        self.a, self.b, self.c, self.d, self.e = (make_user(n) for n in "abcde")
        finished(self.a, self.c)
        finished(self.a, self.c)
        finished(self.b, self.d)
        finished(self.c, self.d)
        self.client.cookies["access_token"] = token_for(self.c)

    def board(self, query=""):
        response = self.client.get(f"/api/game/leaderboard/{query}")
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()["data"]

    def test_order_ratio_then_wins_then_oldest(self):
        data = self.board()
        names = [row["user"]["username"] for row in data["users"]]
        # d lost 2 games (0%), e played none (0%): the older account first.
        self.assertEqual(names, ["a", "b", "c", "d", "e"])
        self.assertEqual([row["rank"] for row in data["users"]], [1, 2, 3, 4, 5])

    def test_pages(self):
        data = self.board("?size=2&page=2")
        self.assertEqual([row["user"]["username"] for row in data["users"]], ["c", "d"])
        self.assertEqual([row["rank"] for row in data["users"]], [3, 4])
        self.assertEqual((data["page"], data["pages"], data["size"], data["total"]), (2, 3, 2, 5))

    def test_page_past_the_end_is_the_last_page(self):
        data = self.board("?size=2&page=99")
        self.assertEqual(data["page"], 3)
        self.assertEqual([row["rank"] for row in data["users"]], [5])

    def test_bad_parameters_use_the_defaults(self):
        for query in ("?page=abc&size=x", "?page=-3&size=0", "?page=&size="):
            with self.subTest(query=query):
                data = self.board(query)
                self.assertEqual((data["page"], data["size"]), (1, 20))

    def test_size_is_capped(self):
        self.assertEqual(self.board("?size=100000")["size"], 100)

    def test_me_is_the_caller(self):
        me = self.board("?size=1")["me"]
        self.assertEqual(
            me,
            {"rank": 3, "total_games": 3, "total_wins": 1, "total_losses": 2, "ratio": 33},
        )

    def test_query_count_does_not_grow_with_users(self):
        def count():
            with CaptureQueriesContext(connection) as ctx:
                self.board("?size=2")
            return len(ctx.captured_queries)

        before = count()
        for i in range(10):
            finished(make_user(f"more{i}"), self.e)
        self.assertEqual(count(), before)


class FriendStatsTests(TestCase):
    def setUp(self):
        self.me = make_user("me")
        self.client.cookies["access_token"] = token_for(self.me)

    def befriend(self, other):
        Friendship.objects.create(
            source_user=self.me, target_user=other, status=Friendship.ACCEPTED
        )

    def friends(self):
        response = self.client.get("/api/friends/")
        self.assertEqual(response.status_code, 200, response.content)
        return {row["friend"]["username"]: row["stats"] for row in response.json()["data"]}

    def test_each_friend_has_stats(self):
        pal, nobody = make_user("pal"), make_user("nobody")
        self.befriend(pal)
        self.befriend(nobody)
        finished(pal, self.me)
        finished(pal, nobody)
        finished(nobody, pal)
        stats = self.friends()
        self.assertEqual(
            stats["pal"], {"total_games": 3, "total_wins": 2, "total_losses": 1, "ratio": 66}
        )
        self.assertEqual(stats["nobody"]["total_games"], 2)

    def test_no_friends(self):
        self.assertEqual(self.friends(), {})

    def test_query_count_does_not_grow_with_friends(self):
        def count():
            with CaptureQueriesContext(connection) as ctx:
                self.friends()
            return len(ctx.captured_queries)

        self.befriend(make_user("first"))
        before = count()
        for i in range(5):
            self.befriend(make_user(f"friend{i}"))
        self.assertEqual(count(), before)

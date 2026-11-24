from unittest import mock

from channels.db import database_sync_to_async
from django.test import TransactionTestCase

from apps.game import game_manager as gm

from .helpers import make_user, token_for


class TournamentBracketTests(TransactionTestCase):
    def setUp(self):
        from apps.game.models import Tournament

        self.players = [make_user(f"p{i}") for i in range(4)]
        self.tournament = Tournament.objects.create(owner=self.players[0])

    def entries(self, t_round):
        from apps.game.models import Tournament_Game

        return list(
            Tournament_Game.objects.filter(tournament=self.tournament, t_round=t_round)
            .select_related("game")
            .order_by("id")
        )

    def test_bracket_is_created_once(self):
        from apps.game.tournament import ensure_bracket

        ensure_bracket(self.tournament)
        ensure_bracket(self.tournament)
        self.assertEqual((len(self.entries(2)), len(self.entries(1))), (2, 1))

    def test_create_tournament_view_builds_bracket(self):
        from apps.game.models import Tournament_Game

        self.client.cookies["access_token"] = token_for(self.players[1])
        response = self.client.post("/api/game/create_tournament/")
        uuid = response.json()["data"]["data"]["uuid"]
        self.assertEqual(Tournament_Game.objects.filter(tournament__uuid=uuid).count(), 3)

    def test_seats_fill_in_order_and_no_double_seat(self):
        from apps.game.tournament import ensure_bracket, take_seat

        ensure_bracket(self.tournament)
        for player in self.players:
            take_seat(self.tournament, player, 2)
        take_seat(self.tournament, self.players[0], 2)  # already seated
        seated = [(e.game.player1_id, e.game.player2_id) for e in self.entries(2)]
        ids = [p.id for p in self.players]
        self.assertEqual(seated, [(ids[0], ids[1]), (ids[2], ids[3])])

    def test_leave_frees_seat_only_without_opponent(self):
        from apps.game.tournament import ensure_bracket, leave_seat, take_seat

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
        from apps.game.tournament import ensure_bracket, take_seat

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
        self.assertEqual(
            (final.player1_id, final.player2_id), (self.players[0].id, self.players[3].id)
        )

        await play(final, 11, 9)
        await database_sync_to_async(self.tournament.refresh_from_db)()
        self.assertTrue(self.tournament.finished)


class TournamentListTests(TransactionTestCase):
    def setUp(self):
        from apps.game.models import Tournament
        from apps.game.tournament import ensure_bracket, take_seat

        self.players = [make_user(f"t{i}") for i in range(6)]
        self.open = Tournament.objects.create(owner=self.players[0])
        ensure_bracket(self.open)
        take_seat(self.open, self.players[0], 2)
        self.half = Tournament.objects.create(owner=self.players[1])
        ensure_bracket(self.half)
        for player in self.players[1:3]:
            take_seat(self.half, player, 2)
        Tournament.objects.create(owner=self.players[3], finished=True)
        self.client.cookies["access_token"] = token_for(self.players[5])

    def test_lists_open_tournaments_with_free_seats(self):
        response = self.client.get("/api/game/get_tournaments/")
        self.assertEqual(response.status_code, 200)
        spots = {t["uuid"]: t["spots"] for t in response.json()["data"]["data"]}
        self.assertEqual(spots, {str(self.open.uuid): 3, str(self.half.uuid): 2})

    def test_query_count_does_not_grow_with_tournaments(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        from apps.game.models import Tournament
        from apps.game.tournament import ensure_bracket

        with CaptureQueriesContext(connection) as small:
            self.client.get("/api/game/get_tournaments/")
        for player in self.players[3:6]:
            ensure_bracket(Tournament.objects.create(owner=player))
        with CaptureQueriesContext(connection) as big:
            self.client.get("/api/game/get_tournaments/")
        self.assertEqual(len(big), len(small))

"""
Tournament bracket helpers (4 players: two round-2 games, one final).

t_round 2 = first round, t_round 1 = final. All writes run in a
transaction with row locks so two players joining or finishing at the
same moment cannot overwrite each other.
"""

from django.db import transaction
from django.db.models import Q

from .models import Game, Tournament, TournamentGame

FIRST_ROUND = 2
FINAL = 1


def ensure_bracket(tournament):
    """Create the 3 bracket games once."""
    with transaction.atomic():
        # Lock the tournament row: the second caller waits, then sees the games.
        Tournament.objects.select_for_update().get(pk=tournament.pk)
        if TournamentGame.objects.filter(tournament=tournament).exists():
            return
        for t_round, count in ((FINAL, 1), (FIRST_ROUND, 2)):
            for _ in range(count):
                TournamentGame.objects.create(
                    tournament=tournament, game=Game.objects.create(), t_round=t_round
                )


def player_filter(user):
    return Q(game__player1=user) | Q(game__player2=user)


def take_seat(tournament, user, t_round):
    """Seat `user` in the first free slot of the round, if not seated yet."""
    with transaction.atomic():
        games = list(
            Game.objects.select_for_update()
            .filter(tournament_games__tournament=tournament, tournament_games__t_round=t_round)
            .order_by("id")
        )
        if any(user.id in (g.player1_id, g.player2_id) for g in games):
            return
        for game in games:
            if game.player1_id is None:
                game.player1 = user
            elif game.player2_id is None:
                game.player2 = user
            else:
                continue
            game.save(update_fields=["player1", "player2"])
            return


def leave_seat(tournament, user, t_round):
    """Free the seat of a player who leaves before an opponent arrived."""
    with transaction.atomic():
        entry = (
            TournamentGame.objects.select_related("game")
            .filter(player_filter(user), tournament=tournament, t_round=t_round)
            .first()
        )
        if entry is None:
            return
        game = Game.objects.select_for_update().get(pk=entry.game_id)
        if game.status != Game.PENDING:
            return
        if game.player1_id == user.id and game.player2_id is None:
            game.player1 = None
        elif game.player2_id == user.id and game.player1_id is None:
            game.player2 = None
        else:
            return
        game.save(update_fields=["player1", "player2"])


def advance_winner(game):
    """
    After a bracket game ends: put the winner into the final, or mark the
    tournament finished after the final. Runs once, server side, so it no
    longer depends on the winner's browser still being connected.
    """
    entry = TournamentGame.objects.filter(game=game).select_related("tournament").first()
    if entry is None or game.winner_id is None:
        return
    with transaction.atomic():
        if entry.t_round == FINAL:
            Tournament.objects.filter(pk=entry.tournament_id).update(finished=True)
            return
        first_round = list(
            TournamentGame.objects.filter(
                tournament_id=entry.tournament_id, t_round=FIRST_ROUND
            ).order_by("id")
        )
        final_entry = TournamentGame.objects.filter(
            tournament_id=entry.tournament_id, t_round=FINAL
        ).first()
        if final_entry is None or entry not in first_round:
            return
        final = Game.objects.select_for_update().get(pk=final_entry.game_id)
        if first_round.index(entry) == 0:
            final.player1_id = game.winner_id
        else:
            final.player2_id = game.winner_id
        final.save(update_fields=["player1", "player2"])

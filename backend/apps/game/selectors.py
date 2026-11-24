"""Read queries: stats, history, leaderboard, tournaments."""

from django.contrib.auth import get_user_model
from django.db.models import Count, Q

from .models import Game, Tournament, Tournament_Game


def finished_games(user):
    """Finished games of `user`, newest first."""
    return (
        Game.objects.filter(Q(player1_id=user) | Q(player2_id=user), status=Game.FINISHED)
        .select_related("player1__profile", "player2__profile")
        .order_by("-id")
    )


def _ratio(wins, total):
    return (wins / total) * 100 if total else 0


def stats(user, games=None):
    """{"total_games", "total_wins", "total_losses", "ratio"} for GameStatsSerializer."""
    games = list(finished_games(user) if games is None else games)
    wins = sum(1 for g in games if _won(user, g))
    return {
        "total_games": len(games),
        "total_wins": wins,
        "total_losses": len(games) - wins,
        "ratio": _ratio(wins, len(games)),
    }


def _won(user, game):
    if game.player1_id == user.id:
        return game.player1_score > game.player2_score
    return game.player2_score > game.player1_score


def history(user, games=None):
    """Finished games seen from `user`'s side (.user, .player and their
    scores, .is_user_winner), as GameHistorySerializer expects."""
    games = list(finished_games(user) if games is None else games)
    for game in games:
        mine_first = game.player1_id == user.id
        game.user, game.player = (game.player1, game.player2) if mine_first else (game.player2, game.player1)
        game.user_score, game.player_score = (
            (game.player1_score, game.player2_score)
            if mine_first
            else (game.player2_score, game.player1_score)
        )
        game.is_user_winner = _won(user, game)
    return games


def leaderboard():
    """Every user with .total_games, .total_wins, .total_losses and .ratio,
    best ratio first. Two queries in total: counts are done in Python."""
    totals, wins = {}, {}
    finished = Game.objects.filter(status=Game.FINISHED).values_list(
        "player1_id", "player2_id", "winner_id"
    )
    for player1_id, player2_id, winner_id in finished:
        for player_id in (player1_id, player2_id):
            if player_id is not None:
                totals[player_id] = totals.get(player_id, 0) + 1
        if winner_id is not None:
            wins[winner_id] = wins.get(winner_id, 0) + 1

    users = list(get_user_model().objects.select_related("profile"))
    for user in users:
        user.total_games = totals.get(user.id, 0)
        user.total_wins = wins.get(user.id, 0)
        user.total_losses = user.total_games - user.total_wins
        user.ratio = _ratio(user.total_wins, user.total_games)
    users.sort(key=lambda user: user.ratio, reverse=True)
    return users


def open_tournaments():
    """Unfinished tournaments with .spots: empty player slots in the first
    round (t_round=2), counted in the same query as the list."""
    first_round = Q(tournament_game__t_round=2)
    return (
        Tournament.objects.filter(finished=False)
        .select_related("owner__profile")
        .annotate(
            spots=Count("tournament_game", filter=first_round & Q(tournament_game__game__player1=None))
            + Count("tournament_game", filter=first_round & Q(tournament_game__game__player2=None))
        )
        .order_by("id")
    )


def tournament_games(tournament):
    return Tournament_Game.objects.select_related("game").filter(tournament=tournament)

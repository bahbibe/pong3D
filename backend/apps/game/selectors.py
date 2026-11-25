"""Read queries: stats, history, leaderboard, tournaments."""

from django.contrib.auth import get_user_model
from django.db.models import Count, Q

from .models import Game, Tournament, TournamentGame


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
        game.user, game.player = (
            (game.player1, game.player2) if mine_first else (game.player2, game.player1)
        )
        game.user_score, game.player_score = (
            (game.player1_score, game.player2_score)
            if mine_first
            else (game.player2_score, game.player1_score)
        )
        game.is_user_winner = _won(user, game)
    return games


def _counts(user_ids=None):
    """Finished games and wins per user id, from one query. Only games of
    `user_ids` when given."""
    finished = Game.objects.filter(status=Game.FINISHED)
    if user_ids is not None:
        finished = finished.filter(Q(player1_id__in=user_ids) | Q(player2_id__in=user_ids))
    totals, wins = {}, {}
    for player1_id, player2_id, winner_id in finished.values_list(
        "player1_id", "player2_id", "winner_id"
    ):
        for player_id in (player1_id, player2_id):
            if player_id is not None:
                totals[player_id] = totals.get(player_id, 0) + 1
        if winner_id is not None:
            wins[winner_id] = wins.get(winner_id, 0) + 1
    return totals, wins


def _stats_of(user_id, totals, wins):
    games, won = totals.get(user_id, 0), wins.get(user_id, 0)
    return {
        "total_games": games,
        "total_wins": won,
        "total_losses": games - won,
        "ratio": _ratio(won, games),
    }


def stats_for(user_ids):
    """{user_id: stats} for these users, in one query (see stats())."""
    ids = list(user_ids)
    totals, wins = _counts(ids)
    return {user_id: _stats_of(user_id, totals, wins) for user_id in ids}


def leaderboard_order():
    """Every user id, best first: ratio, then wins, then the oldest account.
    Two queries; no user rows are loaded. Returns (ids, totals, wins)."""
    totals, wins = _counts()
    ids = get_user_model().objects.values_list("id", flat=True)

    def key(user_id):
        games, won = totals.get(user_id, 0), wins.get(user_id, 0)
        return (-_ratio(won, games), -won, user_id)

    return sorted(ids, key=key), totals, wins


def leaderboard_page(page, size, viewer=None):
    """One page of the leaderboard. Rows are users with .rank and the stats
    attributes LeaderboardSerializer reads; only that page's users are
    loaded. `page` is clamped to the existing pages. "me" is the viewer's
    rank and stats."""
    order, totals, wins = leaderboard_order()
    total = len(order)
    pages = max(1, -(-total // size))
    page = min(max(page, 1), pages)
    start = (page - 1) * size
    ids = order[start : start + size]
    users = get_user_model().objects.select_related("profile").in_bulk(ids)
    rows = []
    for offset, user_id in enumerate(ids):
        user = users[user_id]
        for field, value in _stats_of(user_id, totals, wins).items():
            setattr(user, field, value)
        user.rank = start + offset + 1
        rows.append(user)
    me = None
    if viewer is not None and viewer.id in set(order):
        me = {"rank": order.index(viewer.id) + 1, **_stats_of(viewer.id, totals, wins)}
    return {"rows": rows, "page": page, "pages": pages, "size": size, "total": total, "me": me}


def open_tournaments():
    """Unfinished tournaments with .spots: empty player slots in the first
    round (t_round=2), counted in the same query as the list."""
    first_round = Q(tournament_games__t_round=2)
    return (
        Tournament.objects.filter(finished=False)
        .select_related("owner__profile")
        .annotate(
            spots=Count(
                "tournament_games", filter=first_round & Q(tournament_games__game__player1=None)
            )
            + Count(
                "tournament_games", filter=first_round & Q(tournament_games__game__player2=None)
            )
        )
        .order_by("id")
    )


def tournament_games(tournament):
    return TournamentGame.objects.select_related("game").filter(tournament=tournament)

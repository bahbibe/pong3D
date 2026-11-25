"""Profile and friend pages: match history, friend stats, rank."""

import secrets

from helpers import befriend, finished_game, force_username, register

PAYLOAD = "<img src=x id=e2e-injected>"


def unsafe_name():
    # Usernames are unique: a new one per run.
    return secrets.token_hex(3) + PAYLOAD


def test_friend_history_is_escaped(user_page):
    page, me = user_page, user_page.user
    friend = register()
    finished_game(friend, me)
    # A game whose opponent account was deleted must not break the list.
    finished_game(friend, None)
    force_username(friend, unsafe_name())
    page.goto(f"/friend/{friend.uuid}", wait_until="networkidle")
    history = page.locator("#friend-history")
    history.get_by_text(PAYLOAD).first.wait_for()
    assert page.locator("#e2e-injected").count() == 0
    assert history.locator(".row").count() == 1


def test_own_history_is_escaped(user_page):
    page, me = user_page, user_page.user
    other = register()
    finished_game(me, other)
    force_username(other, unsafe_name())
    page.goto("/profile", wait_until="networkidle")
    page.locator("#games-container").get_by_text(PAYLOAD).first.wait_for()
    assert page.locator("#e2e-injected").count() == 0


def test_friend_stats_and_rank_are_real(user_page):
    page, me = user_page, user_page.user
    friend, other = register(), register()
    befriend(me, friend)
    finished_game(friend, other)
    finished_game(friend, other)
    finished_game(other, friend)
    page.goto("/profile", wait_until="networkidle")
    row = page.locator(f"#friend-{friend.id}")
    row.wait_for()
    assert row.locator(".friend-total").inner_text().strip() == "3"
    assert row.locator(".friend-wins").inner_text().strip() == "2"
    board = me.api("GET", "/api/game/leaderboard/").json()["data"]["users"]
    friend_row = next(r for r in board if r["user"]["id"] == friend.id)
    # The same ratio as the ranking page shows (the API sends an integer).
    assert row.locator(".friend-ratio").inner_text().strip() == f"{friend_row['ratio']}%"
    rank = next(i + 1 for i, r in enumerate(board) if r["user"]["id"] == me.id)
    assert page.locator("#profile-rank").inner_text().strip() == f"#{rank}"


def test_friend_link_stays_in_the_app(user_page):
    page, me = user_page, user_page.user
    friend = register()
    befriend(me, friend)
    page.goto("/profile", wait_until="networkidle")
    page.evaluate("window.__e2e_same_document = true")
    page.locator(f"#friend-{friend.id} a[href='/friend/{friend.uuid}']").click()
    page.wait_for_url(f"**/friend/{friend.uuid}")
    page.locator("#app > friend-page").wait_for()
    assert page.evaluate("window.__e2e_same_document") is True


def test_overlay_hides_when_friends_fail_to_load(user_page, errors):
    page = user_page
    page.route("**/api/friends/", lambda route: route.abort())
    page.goto("/profile", wait_until="networkidle")
    page.locator("#overlay").wait_for(state="hidden")
    # The aborted request and the page logging it are the point of this test.
    errors[:] = [e for e in errors if "/api/friends/" not in e and "Failed to fetch" not in e]

"""Score, matchmaking and tournament list pages."""

from helpers import BASE, finished_game, register


def test_score_page_of_a_bot_game(user_page):
    page = user_page
    page.goto("/score/bot?player1_score=3&player2_score=1", wait_until="networkidle")
    assert page.locator("#player1_score").text_content() == "3"
    assert page.locator("#player2_score").text_content() == "1"
    assert page.locator("score-page .player1 img").count() == 1
    page.locator("score-page a", has_text="Leave").click()
    page.wait_for_url("**/home")
    page.locator("#app > user-home").wait_for()


def test_score_page_play_again(user_page):
    page, me = user_page, user_page.user
    other = register()
    game_id = finished_game(me, other, 3, 1)
    page.goto(f"/score/{game_id}", wait_until="networkidle")
    assert page.locator("#player1_score").text_content() == "3"
    assert page.locator("#player2_score").text_content() == "1"
    page.locator("#invite_game").click()
    page.wait_for_url("**/play/*")
    new_id = int(page.url.rsplit("/", 1)[1])
    assert new_id > game_id


def test_matchmaking_leave_goes_home(user_page):
    page = user_page
    page.goto("/matchmaking", wait_until="networkidle")
    page.locator("matchmaking-page #loader-message", has_text="Looking for a match").wait_for()
    page.locator("matchmaking-page a", has_text="Leave").click()
    page.wait_for_url("**/home")
    page.locator("#app > user-home").wait_for()


def test_join_lists_open_tournaments(user_page):
    page = user_page
    owner = register()
    created = owner.api("POST", "/api/game/create_tournament/").json()
    uuid = created["data"]["data"]["uuid"]
    page.goto("/join", wait_until="networkidle")
    link = page.locator(f"join-page a[href='/tournament/{uuid}']")
    link.click()
    page.wait_for_url(f"**/tournament/{uuid}")
    page.locator("#app > tournament-display-page").wait_for()
    assert page.url == BASE + f"/tournament/{uuid}"

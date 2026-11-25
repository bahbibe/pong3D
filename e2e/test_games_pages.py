"""Score, matchmaking and tournament list pages."""

from helpers import BASE, Sockets, finished_game, register, wait_until


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


def test_bot_game_keys_and_leaving(user_page):
    page = user_page
    sockets, sent = Sockets(page), []
    page.on(
        "websocket",
        lambda ws: (
            "/ws/game/" in ws.url and ws.on("framesent", lambda frame: sent.append(str(frame)))
        ),
    )
    page.goto("/play/bot", wait_until="networkidle", timeout=120_000)
    wait_until(lambda: sockets.open("/ws/game/bot"), message="game socket", page=page)

    def holding_left_sends_right():
        # Keys count once the 3D scene is loaded: keep pressing until then.
        page.keyboard.down("ArrowLeft")
        return any('"direction":"right"' in frame for frame in sent)

    wait_until(holding_left_sends_right, timeout=60, message="move right sent", page=page)
    page.keyboard.up("ArrowLeft")
    wait_until(
        lambda: any('"direction":"none"' in frame for frame in sent),
        message="stop sent",
        page=page,
    )
    page.evaluate("async () => (await import('/static/js/core/router.js')).navigate('/home')")
    page.locator("#app > user-home").wait_for()
    wait_until(lambda: not sockets.open("/ws/game/bot"), message="game socket closed", page=page)

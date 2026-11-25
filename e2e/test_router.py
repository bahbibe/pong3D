"""The client-side router: session caching, stale navigations, guards,
history, titles, query strings and links."""

from helpers import BASE, nav_click, register, wait_until


def test_one_session_request_per_page_load(user_page):
    page = user_page
    me_calls = []
    page.on("request", lambda r: r.url.endswith("/api/auth/me/") and me_calls.append(r.url))
    page.goto("/home", wait_until="networkidle")
    for path, tag in [
        ("/ranking", "ranking-page"),
        ("/profile", "user-profile"),
        ("/chat", "chat-page"),
        ("/settings", "settings-page"),
    ]:
        nav_click(page, f"a[href='{path}']")
        page.wait_for_url(f"**{path}")
        page.locator(f"#app > {tag}").wait_for()
    page.go_back()
    page.locator("#app > chat-page").wait_for()
    assert len(me_calls) == 1


def test_a_newer_navigation_wins(user_page):
    page = user_page
    page.goto("/home", wait_until="networkidle")
    # Slow down the session check that the redirect of /login triggers.
    page.route(
        "**/api/auth/me/",
        lambda route: (page.wait_for_timeout(1500), route.continue_()),
    )
    page.evaluate(
        """async () => {
            const { navigate } = await import('/static/js/core/router.js');
            navigate('/login');      // logged in: re-checks the session, slowly
            navigate('/ranking');    // cached session: renders at once
        }"""
    )
    page.locator("#app > ranking-page").wait_for()
    page.wait_for_timeout(2500)  # the slow check is over
    assert page.url == BASE + "/ranking"
    assert page.locator("#app > ranking-page").count() == 1
    assert page.locator("#app > user-home").count() == 0


def test_unknown_path_logged_in_keeps_the_url(user_page):
    user_page.goto("/no/such/page", wait_until="networkidle")
    user_page.locator("#app > not-found-page").wait_for()
    assert user_page.url == BASE + "/no/such/page"


def test_malformed_path_is_not_found(user_page):
    # Valid %-escapes, invalid UTF-8: decodeURIComponent throws on it.
    user_page.goto("/friend/%E0%A4", wait_until="networkidle")
    user_page.locator("#app > not-found-page").wait_for()


def test_guard_redirect_does_not_trap_the_back_button(page, errors):
    errors.watch(page)
    page.goto("about:blank")
    page.goto("/profile", wait_until="networkidle")
    assert page.url == BASE + "/login"
    page.go_back()
    assert page.url == "about:blank"


def test_page_titles(user_page):
    user_page.goto("/ranking", wait_until="networkidle")
    assert user_page.title() == "Ranking · PONG"
    user_page.goto("/no-such-page", wait_until="networkidle")
    assert user_page.title() == "Not found · PONG"


def test_ctrl_click_opens_a_new_tab(user_page, context):
    page = user_page
    page.goto("/home", wait_until="networkidle")
    page.locator("main-nav .user").first.hover()
    with context.expect_page() as new_tab:
        page.locator("main-nav .dropdown-content a[href='/ranking']").first.click(
            modifiers=["Control"]
        )
    new_tab.value.wait_for_load_state()
    assert new_tab.value.url == BASE + "/ranking"
    assert page.url == BASE + "/home"


def test_search_query_is_in_the_url(user_page):
    page = user_page
    target = register()
    page.goto("/home", wait_until="networkidle")
    page.locator("main-nav search-bar [data-search]").fill(target.username)
    page.locator("main-nav search-bar [data-search]").press("Enter")
    page.wait_for_url(f"**/search?q={target.username}")
    result = page.locator("#search-container").get_by_text(target.username)
    result.wait_for()
    # The URL is enough: reloading (or sharing it) shows the same results.
    page.reload(wait_until="networkidle")
    result.wait_for()
    page.evaluate("window.__e2e_same_document = true")
    result.click()
    page.wait_for_url(f"**/friend/{target.uuid}")
    assert page.evaluate("window.__e2e_same_document") is True


def test_api_401_sends_to_login(user_page, context):
    page, me = user_page, user_page.user
    page.goto("/home", wait_until="networkidle")
    # Logging out elsewhere revokes every session of the user.
    assert me.api("POST", "/api/auth/logout/").ok
    status = page.evaluate(
        """async () => {
            const { api } = await import('/static/js/core/api.js');
            return (await api.get('/api/friends/')).status;
        }"""
    )
    assert status == 401
    wait_until(lambda: page.url == BASE + "/login", timeout=10, message="/login", page=page)
    page.locator("#app > login-page").wait_for()

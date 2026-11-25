"""Every page renders its element without errors; the route guards."""

import pytest

from helpers import BASE, nav_click, register

PAGES = {
    "/home": "user-home",
    "/profile": "user-profile",
    "/settings": "settings-page",
    "/ranking": "ranking-page",
    "/search": "search-page",
    "/chat": "chat-page",
    "/matchmaking": "matchmaking-page",
    "/tournament": "tour-page",
    "/join": "join-page",
}

# Labels and names for what a screen reader needs (from the old browser smoke).
A11Y_JS = """() => {
  const name = el => (el.getAttribute('aria-label') || el.getAttribute('title') || el.textContent || '').trim()
    || [...el.querySelectorAll('img[alt]')].map(i => i.alt).join('').trim();
  const vis = el => el.offsetParent !== null;
  const out = [];
  if (!document.documentElement.lang) out.push('html without lang');
  document.querySelectorAll('#app img').forEach(i => {
    if (vis(i) && !i.hasAttribute('alt')) out.push('img without alt: ' + i.src.split('/').pop());
  });
  document.querySelectorAll('#app button, #app a').forEach(b => {
    if (vis(b) && !name(b)) out.push(b.tagName + ' without a name: ' + b.outerHTML.slice(0, 90));
  });
  document.querySelectorAll('#app input:not([type=hidden]):not([type=file])').forEach(i => {
    const labelled = i.labels?.length || i.getAttribute('aria-label') || i.getAttribute('aria-labelledby');
    if (vis(i) && !labelled) out.push('input without label: ' + (i.id || i.name));
  });
  return [...new Set(out)];
}"""


@pytest.mark.parametrize("path,tag", PAGES.items())
def test_page_renders(user_page, path, tag):
    page = user_page
    page.goto(path, wait_until="networkidle")
    assert page.url == BASE + path
    page.locator(f"#app > {tag}").wait_for()
    page.locator("#app main-nav").first.wait_for()
    assert page.evaluate(A11Y_JS) == []


def test_friend_page(user_page):
    other = register()
    user_page.goto(f"/friend/{other.uuid}", wait_until="networkidle")
    user_page.locator("#app > friend-page").wait_for()
    user_page.get_by_text(other.username).first.wait_for()


def test_tournament_page(user_page):
    created = user_page.user.api("POST", "/api/game/create_tournament/").json()
    assert created["success"], created
    uuid = created["data"]["data"]["uuid"]
    user_page.goto(f"/tournament/{uuid}", wait_until="networkidle")
    user_page.locator("#app > tournament-display-page").wait_for()


def test_bot_game_draws(user_page):
    user_page.goto("/play/bot", wait_until="networkidle", timeout=120_000)
    canvas = user_page.locator("#game-canvas")
    canvas.wait_for()
    box = canvas.bounding_box()
    assert box and box["width"] > 100 and box["height"] > 100


def test_logged_out_is_sent_to_login(page, errors):
    errors.watch(page)
    page.goto("/home", wait_until="networkidle")
    assert page.url == BASE + "/login"
    page.locator("#app > login-page").wait_for()


def test_logged_in_landing_goes_home(user_page):
    user_page.goto("/", wait_until="networkidle")
    assert user_page.url == BASE + "/home"


def test_not_set_up_goes_to_setup(context, page, errors):
    fresh = register(setup=False)
    fresh.login_context(context)
    errors.watch(page)
    page.goto("/home", wait_until="networkidle")
    assert page.url == BASE + "/setup"


def test_unknown_path_logged_out(page, errors):
    errors.watch(page)
    page.goto("/no-such-page", wait_until="networkidle")
    page.locator("#app > not-found-page").wait_for()


def test_links_navigate_without_reload(user_page):
    page = user_page
    page.goto("/home", wait_until="networkidle")
    page.evaluate("window.__e2e_same_document = true")
    nav_click(page, "a[href='/ranking']")
    page.wait_for_url("**/ranking")
    page.locator("#app > ranking-page").wait_for()
    assert page.evaluate("window.__e2e_same_document") is True
    page.go_back()
    page.wait_for_url("**/home")
    page.locator("#app > user-home").wait_for()


def test_static_cache_headers():
    import requests

    def cache_control(path):
        response = requests.head(BASE + path, verify=False, timeout=10)
        assert response.status_code == 200, path
        return response.headers.get("Cache-Control", "")

    # Modules are revalidated on every load, so a deploy never mixes versions.
    assert cache_control("/static/js/router.js") == "no-cache"
    assert cache_control("/static/css/index.css") == "no-cache"
    assert "immutable" in cache_control("/static/vendor/three-0.170.0/build/three.module.min.js")
    assert "max-age=86400" in cache_control("/static/scene.glb")
    # The security headers are still there.
    response = requests.head(BASE + "/static/js/router.js", verify=False, timeout=10)
    assert response.headers["X-Content-Type-Options"] == "nosniff"

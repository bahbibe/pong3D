"""Register, login, setup, settings, 2FA and logout through the UI."""

import secrets

from helpers import (
    BASE,
    PASSWORD,
    Sockets,
    nav_click,
    next_code,
    png,
    pyotp,
    register,
    tfa_secret,
    wait_until,
)


def test_register_login_and_setup(page, errors):
    errors.watch(page)
    name = "r" + secrets.token_hex(4)
    page.goto("/login", wait_until="networkidle")
    page.click("#tab-register")
    page.fill("#firstName", "Reg")
    page.fill("#lastName", "Ister")
    page.fill("#register-form #username", name)
    page.fill("#register-form #email", f"{name}@e2e.test")
    page.fill("#register-form #password", PASSWORD)
    page.fill("#register-form #confirm-password", PASSWORD)
    page.click("[data-register]")
    page.locator("#toast-wrapper .toast.show.text-bg-success").wait_for()

    page.fill("[data-email]", f"{name}@e2e.test")
    page.fill("[data-password]", PASSWORD)
    page.click("[data-login]")
    page.wait_for_url("**/setup")
    page.fill("setup-page #username", name + "x")
    page.click("setup-page button[type=submit]")
    page.wait_for_url("**/home")
    page.locator("#app > user-home").wait_for()


def test_wrong_password_shows_an_error(page, errors, user):
    errors.watch(page)
    page.goto("/login", wait_until="networkidle")
    page.fill("[data-email]", user.email)
    page.fill("[data-password]", "Not-The-Password-1")
    page.click("[data-login]")
    page.locator("#toast-wrapper .toast.show.text-bg-danger").wait_for()
    assert page.url == BASE + "/login"


def test_settings_username_and_avatar(user_page):
    page, user = user_page, user_page.user
    page.goto("/settings", wait_until="networkidle")
    assert page.input_value("settings-page #email") == user.email
    page.set_input_files(
        "settings-page .file-upload",
        files=[{"name": "a.png", "mimeType": "image/png", "buffer": png()}],
    )
    page.fill("settings-page #username", user.username + "y")
    page.click("#settings-form button[type=submit]")
    page.wait_for_url("**/profile")
    # The profile shows the new name (from the update's answer, no reload).
    assert page.locator("user-profile #username").text_content() == f"@{user.username}y"
    me = user.api("GET", "/api/auth/me/").json()["data"]["user"]
    assert me["username"] == user.username + "y"
    assert "profile_default" not in me["profile"]["avatar"]


def test_enable_and_disable_2fa(user_page):
    page, user = user_page, user_page.user
    page.goto("/settings", wait_until="networkidle")
    confirms = []
    page.on("request", lambda r: "/twofa/confirm/" in r.url and confirms.append(r.url))
    # Opening the modal twice must still send one confirm request.
    page.click("settings-page #enable-2fa")
    page.locator("settings-page #twoFaModal.show").wait_for()
    page.click("settings-page #twoFaModal .close")
    page.locator("settings-page #twoFaModal.show").wait_for(state="detached")
    page.click("settings-page #enable-2fa")
    page.locator("settings-page #twoFaModal.show").wait_for()

    totp = pyotp.TOTP(tfa_secret(user.username))
    page.fill("settings-page #twofa-code", totp.now())
    # Enter confirms the code; it must not submit the settings form around it.
    page.press("settings-page #twofa-code", "Enter")
    page.locator("settings-page #disable-2fa").wait_for(state="visible")
    assert len(confirms) == 1
    assert page.url.endswith("/settings")

    code = next_code(totp)
    page.once("dialog", lambda d: d.accept(code))
    page.click("settings-page #disable-2fa")
    page.locator("settings-page #enable-2fa").wait_for(state="visible")
    me = user.api("GET", "/api/auth/me/").json()["data"]["user"]
    assert me["profile"]["is_tfa_enabled"] is False


def test_login_with_2fa(page, errors):
    user = register()
    assert user.api("POST", "/api/auth/twofa/enable/").json()["success"]
    totp = pyotp.TOTP(tfa_secret(user.username))
    assert user.api("POST", "/api/auth/twofa/confirm/", json={"code": totp.now()}).json()["success"]

    errors.watch(page)
    page.goto("/login", wait_until="networkidle")
    page.fill("[data-email]", user.email)
    page.fill("[data-password]", PASSWORD)
    page.click("[data-login]")
    page.wait_for_url("**/twofa")
    # Every other page sends you back to the code until it is entered. The
    # page you asked for must not render meanwhile (it used to, and threw).
    page.goto("/home", wait_until="networkidle")
    assert page.url == BASE + "/twofa"
    page.fill("#twofa-code", next_code(totp))
    page.click("#verify-twofa")
    page.wait_for_url("**/home")
    page.locator("#app > user-home").wait_for()


def test_logout_closes_the_sockets(user_page):
    page = user_page
    sockets = Sockets(page)
    page.goto("/home", wait_until="networkidle")
    wait_until(
        lambda: sockets.open("/ws/status/") and sockets.open("/ws/notifications/"),
        message="status and notification sockets",
        page=page,
    )
    nav_click(page, "#logout")
    page.wait_for_url("**/login")
    wait_until(
        lambda: not sockets.open("/ws/status/") and not sockets.open("/ws/notifications/"),
        message="sockets closed after logout",
        page=page,
    )
    me = page.request.get("/api/auth/me/")
    assert me.status == 401


def test_login_network_error_shows_a_toast_and_unblocks(page, errors, user):
    errors.watch(page)
    page.goto("/login", wait_until="networkidle")
    page.route("**/api/auth/login/", lambda route: route.abort())
    page.fill("[data-email]", user.email)
    page.fill("[data-password]", PASSWORD)
    page.click("[data-login]")
    page.locator("#toast-wrapper .toast.show.text-bg-danger").wait_for()
    page.locator("#overlay").wait_for(state="hidden")
    errors[:] = [e for e in errors if "/api/auth/login/" not in e]


def test_intra_failure_shows_a_toast(page, errors):
    errors.watch(page)
    page.goto("/login", wait_until="networkidle")
    page.route(
        "**/api/auth/intra/",
        lambda route: route.fulfill(
            status=503,
            content_type="application/json",
            body='{"success": false, "message": "42 intra is not reachable"}',
        ),
    )
    page.click("#intra")
    page.locator("#toast-wrapper .toast.show", has_text="42 intra is not reachable").wait_for()
    page.locator("#overlay").wait_for(state="hidden")
    errors[:] = [e for e in errors if "/api/auth/intra/" not in e]  # the mocked 503


def test_leaving_settings_with_the_2fa_modal_open(user_page):
    page = user_page
    page.goto("/settings", wait_until="networkidle")
    page.click("settings-page #enable-2fa")
    page.locator("settings-page #twoFaModal.show").wait_for()
    page.evaluate("async () => (await import('/static/js/core/router.js')).navigate('/home')")
    page.locator("#app > user-home").wait_for()
    assert page.locator(".modal-backdrop").count() == 0
    assert "modal-open" not in (page.locator("body").get_attribute("class") or "")

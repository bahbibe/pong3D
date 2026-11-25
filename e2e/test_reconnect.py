"""The status and notification sockets come back after a backend restart,
and notifications missed meanwhile are loaded again."""

import time

from helpers import Sockets, compose, register, wait_until


def test_sockets_reopen_after_backend_restart(user_page, errors):
    page, me = user_page, user_page.user
    sockets = Sockets(page)
    me_calls = []
    page.on("request", lambda r: "/api/auth/me/" in r.url and me_calls.append(time.time()))
    page.goto("/home", wait_until="networkidle")
    wait_until(
        lambda: sockets.open("/ws/status/") and sockets.open("/ws/notifications/"),
        message="sockets open",
        page=page,
    )
    before = len(sockets.opened("/ws/notifications/"))

    compose("restart", "backend")
    restarted = time.time()
    wait_until(
        lambda: (
            len(sockets.opened("/ws/notifications/")) > before
            and sockets.open("/ws/status/")
            and sockets.open("/ws/notifications/")
        ),
        timeout=90,
        message="sockets reopened",
        page=page,
    )
    # Handshakes fail with 502 while the backend is down: expected here.
    errors[:] = [e for e in errors if "Unexpected response code: 502" not in e]
    # The notification list is fetched again after the reconnect.
    wait_until(
        lambda: any(t > restarted for t in me_calls), timeout=10, message="resync", page=page
    )

    other = register()
    assert other.api("POST", "/api/friends/send/", json={"target_user": me.id}).ok
    counter = page.locator("main-nav [data-count]").first
    wait_until(
        lambda: counter.text_content() == "1", timeout=10, message="live notification", page=page
    )

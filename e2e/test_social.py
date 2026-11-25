"""Friend requests, notifications and presence: websockets and the nav bell."""

import asyncio
import json

from helpers import Sockets, befriend, register, run_async, wait_until, ws_connect


async def recv_json(socket, timeout=5):
    return json.loads(await asyncio.wait_for(socket.recv(), timeout))


def test_friend_request_notification_over_the_socket():
    a, b = register(), register()

    async def run():
        async with ws_connect("/ws/notifications/", b) as notes:
            assert a.api("POST", "/api/friends/send/", json={"target_user": b.id}).ok
            message = await recv_json(notes)
            assert message["ctx"] == "friend_request"
            assert message["sender"]["username"] == a.username
            assert message.get("notification_uuid") or message.get("uuid")

    run_async(run())


def test_game_invite_notification():
    a, b = register(), register()
    befriend(a, b)

    async def run():
        async with ws_connect("/ws/notifications/", b) as notes:
            assert a.api("POST", f"/api/game/invite_friend/{b.id}").ok
            message = await recv_json(notes)
            assert message["ctx"] == "game_invite"
            assert message["game_id"]

    run_async(run())


def test_presence_online_and_offline():
    a, b = register(), register()
    befriend(a, b)

    async def run():
        async with ws_connect("/ws/status/", b) as watcher:
            await recv_json(watcher)  # b's own online event
            async with ws_connect("/ws/status/", a):
                message = await recv_json(watcher)
                assert message["status"] == "online"
                assert str(a.id) in [str(i) for i in message["online_users"]]
            message = await recv_json(watcher)
            assert message["status"] == "offline"
            assert str(message["user_id"]) == str(a.id)

    run_async(run())


def test_live_notification_in_the_nav(user_page):
    page, me = user_page, user_page.user
    sockets = Sockets(page)
    page.goto("/home", wait_until="networkidle")
    wait_until(lambda: sockets.open("/ws/notifications/"), message="notification socket", page=page)
    other = register()
    assert other.api("POST", "/api/friends/send/", json={"target_user": me.id}).ok
    counter = page.locator("main-nav [data-count]").first
    wait_until(lambda: counter.text_content() == "1", timeout=10, message="counter at 1", page=page)

    page.locator("main-nav #notification-wrapper .dropdown-toggle").first.click()
    page.locator("main-nav .notification-list button").first.click()
    page.wait_for_url(f"**/friend/{other.uuid}")
    unread = me.api("GET", "/api/auth/me/").json()["data"]["notifications"]
    assert unread == []


def test_mark_all_as_read(user_page):
    page, me = user_page, user_page.user
    other = register()
    assert other.api("POST", "/api/friends/send/", json={"target_user": me.id}).ok
    page.goto("/home", wait_until="networkidle")
    page.locator("main-nav #notification-wrapper .dropdown-toggle").first.click()
    page.locator("main-nav #notification-btn").first.click()
    wait_until(
        lambda: me.api("GET", "/api/auth/me/").json()["data"]["notifications"] == [],
        timeout=5,
        message="no unread notifications",
        page=page,
    )
    assert page.locator("main-nav [data-count]").first.text_content() == "0"


def test_open_bell_stays_open_when_a_notification_arrives(user_page):
    page, me = user_page, user_page.user
    sockets = Sockets(page)
    page.goto("/home", wait_until="networkidle")
    wait_until(lambda: sockets.open("/ws/notifications/"), message="notification socket", page=page)
    page.locator("main-nav #notification-wrapper .dropdown-toggle").first.click()
    menu = page.locator("main-nav .notification-ui_dd.show")
    menu.wait_for()
    other = register()
    assert other.api("POST", "/api/friends/send/", json={"target_user": me.id}).ok
    page.locator("main-nav .notification-list", has_text=other.username).wait_for()
    assert menu.count() == 1

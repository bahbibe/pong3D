"""Two friends chat in their browsers."""

import secrets

from helpers import Sockets, befriend, new_context, register, wait_until


def open_chat_with(page, friend, sockets):
    """Open the conversation and wait until its socket is connected (the
    message box shows before that)."""
    before = len(sockets.opened("/ws/chat/"))
    page.goto("/chat", wait_until="networkidle")
    page.locator("friends-list .contact", has_text=friend.username).click()
    page.locator("chat-box .msg-box").wait_for()
    wait_until(
        lambda: (
            len(sockets.opened("/ws/chat/")) > before
            and any(not ws.is_closed() for ws in sockets.all if "/ws/chat/" in ws.url)
        ),
        timeout=10,
        message="chat socket open",
        page=page,
    )


def test_message_goes_both_ways(browser, errors):
    a, b = register(), register()
    befriend(a, b)
    ctx_a, ctx_b = new_context(browser, a), new_context(browser, b)
    page_a, page_b = errors.watch(ctx_a.new_page()), errors.watch(ctx_b.new_page())
    sockets_a, sockets_b = Sockets(page_a), Sockets(page_b)
    open_chat_with(page_a, b, sockets_a)
    open_chat_with(page_b, a, sockets_b)

    text = "hello " + secrets.token_hex(3)
    page_a.fill("chat-box .send-input", text)
    page_a.press("chat-box .send-input", "Enter")
    page_b.locator("chat-box .msg-received", has_text=text).wait_for(timeout=5000)
    page_a.locator("chat-box .msg-sent", has_text=text).wait_for(timeout=5000)

    reply = "<b>bold?</b> " + secrets.token_hex(3)
    page_b.fill("chat-box .send-input", reply)
    page_b.press("chat-box .send-input", "Enter")
    received = page_a.locator("chat-box .msg-received", has_text=reply)
    received.wait_for(timeout=5000)
    # Shown as text, not as markup.
    assert received.locator("b").count() == 0

    # History is loaded when the chat opens again.
    open_chat_with(page_a, b, sockets_a)
    wait_until(
        lambda: page_a.locator("chat-box .msg-box", has_text=reply).count() == 1,
        timeout=5,
        message="history",
        page=page_a,
    )
    ctx_a.close()
    ctx_b.close()


def test_contact_opens_the_right_conversation(browser, errors):
    me, first, second = register(), register(), register()
    befriend(me, first)
    befriend(me, second)
    ctx = new_context(browser, me)
    page = errors.watch(ctx.new_page())
    sockets = Sockets(page)
    page.goto("/chat", wait_until="networkidle")
    assert page.get_by_text("lore ipsum").count() == 0
    open_chat_with(page, second, sockets)
    page.locator("chat-box .msg-head", has_text=second.username).wait_for()
    # Empty conversation: the placeholder goes with the first message.
    page.locator("chat-box #empty").wait_for()
    page.fill("chat-box .send-input", "first message")
    page.press("chat-box .send-input", "Enter")
    page.locator("chat-box .msg-sent", has_text="first message").wait_for()
    assert page.locator("chat-box #empty").count() == 0
    ctx.close()

"""Two friends chat in their browsers."""

import secrets

from helpers import befriend, new_context, register, wait_until


def open_chat_with(page, friend):
    page.goto("/chat", wait_until="networkidle")
    page.locator("friends-list .contact", has_text=friend.username).click()
    page.locator("chat-box .msg-box").wait_for()


def test_message_goes_both_ways(browser, errors):
    a, b = register(), register()
    befriend(a, b)
    ctx_a, ctx_b = new_context(browser, a), new_context(browser, b)
    page_a, page_b = errors.watch(ctx_a.new_page()), errors.watch(ctx_b.new_page())
    open_chat_with(page_a, b)
    open_chat_with(page_b, a)

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
    open_chat_with(page_a, b)
    wait_until(
        lambda: page_a.locator("chat-box .msg-box", has_text=reply).count() == 1,
        timeout=5,
        message="history",
        page=page_a,
    )
    ctx_a.close()
    ctx_b.close()

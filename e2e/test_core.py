"""The core modules (frontend/static/js/core), run in a real page: they are
imported with import() from the served files."""

import pytest


@pytest.fixture
def core(user_page):
    user_page.goto("/home", wait_until="networkidle")
    return user_page


def test_html_escapes_values(core):
    out = core.evaluate(
        """async () => {
            const { html, raw } = await import('/static/js/core/html.js');
            const name = '<script>alert(1)</script>';
            const attr = '" onmouseover="x';
            const items = ['<a>', 'b&c'];
            return {
                text: String(html`<p>${name}</p>`),
                attr: String(html`<img alt="${attr}">`),
                nested: String(html`<ul>${items.map((i) => html`<li>${i}</li>`)}</ul>`),
                empty: String(html`${null}${undefined}${false}${true}${0}`),
                raw: String(html`<div>${raw('<b>ok</b>')}</div>`),
            };
        }"""
    )
    assert out["text"] == "<p>&lt;script&gt;alert(1)&lt;/script&gt;</p>"
    assert out["attr"] == '<img alt="&quot; onmouseover=&quot;x">'
    assert out["nested"] == "<ul><li>&lt;a&gt;</li><li>b&amp;c</li></ul>"
    assert out["empty"] == "0"
    assert out["raw"] == "<div><b>ok</b></div>"


def test_render_takes_templates_only(core):
    error = core.evaluate(
        """async () => {
            const { render } = await import('/static/js/core/html.js');
            try { render(document.createElement('div'), '<b>x</b>'); return null; }
            catch (e) { return e.constructor.name; }
        }"""
    )
    assert error == "TypeError"


def test_store_subscribe_and_abort(core):
    calls = core.evaluate(
        """async () => {
            const { createStore } = await import('/static/js/core/store.js');
            const store = createStore(1);
            const seen = [];
            const controller = new AbortController();
            store.subscribe((v) => seen.push(v), { signal: controller.signal });
            store.set(2);
            store.set((v) => v + 1);
            controller.abort();
            store.set(10);
            return { seen, value: store.get() };
        }"""
    )
    assert calls == {"seen": [2, 3], "value": 10}


def test_api_results(core, errors):
    core.route("**/api/game/get_game/999999999", lambda route: route.abort())
    out = core.evaluate(
        """async () => {
            const { api } = await import('/static/js/core/api.js');
            return {
                ok: await api.get('/api/game/leaderboard/'),
                invalid: await api.post('/api/friends/send/', { target_user: 'x' }),
                network: await api.get('/api/game/get_game/999999999'),
            };
        }"""
    )
    assert out["ok"]["ok"] is True and isinstance(out["ok"]["data"]["users"], list)
    assert out["invalid"]["ok"] is False and out["invalid"]["status"] == 400
    assert out["invalid"]["errors"] or out["invalid"]["message"]
    errors[:] = [e for e in errors if "999999999" not in e]  # the aborted request
    assert out["network"] == {
        "ok": False,
        "status": 0,
        "message": "Network error, please try again.",
        "errors": {},
    }

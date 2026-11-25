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


def test_component_cleans_up_on_removal(core):
    result = core.evaluate(
        """async () => {
            const { Component } = await import('/static/js/core/page.js');
            const { createStore } = await import('/static/js/core/store.js');
            const store = createStore(0);
            const log = { clicks: 0, timer: false, store: [], fetch: null, closed: false };
            class TestElement extends Component {
                mount() {
                    this.on(document, 'click', () => log.clicks++);
                    this.timeout(() => { log.timer = true; }, 200);
                    this.subscribe(store, (v) => log.store.push(v));
                    this.api.get('/api/game/leaderboard/').then((r) => { log.fetch = r; });
                    const ws = this.socket('/ws/status/');
                    ws.addEventListener('close', () => { log.closed = true; });
                }
            }
            customElements.define('e2e-test-element', TestElement);
            const el = document.createElement('e2e-test-element');
            document.body.append(el);
            document.body.click();
            el.remove();                 // before the request answers
            document.body.click();
            store.set(1);
            await new Promise((r) => setTimeout(r, 600));
            return log;
        }"""
    )
    assert result["clicks"] == 1
    assert result["timer"] is False
    assert result["store"] == [0]
    assert result["fetch"]["aborted"] is True
    assert result["closed"] is True


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


INTERPOLATION_JS = """async () => {
    const { createInterpolator } = await import('/static/js/core/interpolation.js');
    const at = (delay = 50) => createInterpolator({ delay, maxExtrapolation: 100, snapDistance: 1 });
    const out = {};

    let m = at();
    out.empty = m.sample(1000);
    m.push({ x: 0 }, 1000);
    out.single = m.sample(2000);

    // Between two updates: blended at render time = now - delay.
    m = at();
    m.push({ x: 0 }, 1000);
    m.push({ x: 0.5 }, 1020);
    out.before = m.sample(1040).x;      // render time 990: oldest, not enough history
    out.middle = m.sample(1060).x;      // render time 1010: halfway
    out.atNewer = m.sample(1070).x;     // render time 1020: the newer one

    // Past the newest update: continues the motion, at most 100 ms.
    out.extrapolated = m.sample(1080).x;   // 10 ms ahead at 0.025/ms
    out.capped = m.sample(5000).x;         // capped at 100 ms ahead

    // A jump bigger than snapDistance does not glide.
    m = at();
    m.push({ x: 4.9 }, 1000);
    m.push({ x: 0 }, 1020);
    out.snapped = m.sample(1060).x;
    out.snappedAhead = m.sample(1200).x;

    // Every value is blended on its own.
    m = at();
    m.push({ a: 0, b: 10 }, 1000);
    m.push({ a: 1, b: 10.5 }, 1100);
    out.fields = m.sample(1100);       // render time 1050

    // With sending times, jittered arrivals land on the sender's clock:
    // sent every 20 ms, arrived 100-130 ms later. The offset is the fastest
    // delivery (100 ms), so at 200 the render time is 50 on the sender's clock.
    m = at();
    const sent = [0, 20, 40, 60, 80];
    const arrived = [100, 135, 141, 170, 185];
    sent.forEach((t, k) => m.push({ x: k * 0.1 }, arrived[k], t));
    out.senderClock = m.sample(200).x;
    m.push({ x: 9 }, 190, 30);  // older than the newest: ignored
    out.ignoredSize = m.size;

    // Old snapshots are dropped.
    m = createInterpolator({ keep: 1000 });
    for (let t = 0; t <= 10000; t += 16) m.push({ x: t }, t);
    out.size = m.size;
    return out;
}"""


def test_interpolation(core):
    out = core.evaluate(INTERPOLATION_JS)
    assert out["empty"] is None
    assert out["single"] == {"x": 0}
    assert out["before"] == 0
    assert out["middle"] == 0.25
    assert out["atNewer"] == 0.5
    assert abs(out["extrapolated"] - 0.75) < 1e-9
    assert abs(out["capped"] - 3.0) < 1e-9
    assert out["snapped"] == 0
    assert out["snappedAhead"] == 0
    assert out["fields"] == {"a": 0.5, "b": 10.25}
    assert abs(out["senderClock"] - 0.25) < 1e-9
    assert out["ignoredSize"] == 5
    assert out["size"] < 70

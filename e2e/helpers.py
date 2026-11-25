"""Helpers shared by the tests. The tests run on the host against a running stack
(`make dev`, then `make e2e`). E2E_BASE_URL picks the stack (default dev),
E2E_COMPOSE the compose command used to read the database (2FA secrets)
and to restart the backend."""

import asyncio
import os
import secrets
import shlex
import ssl
import struct
import subprocess
import threading
import time
import zlib
from dataclasses import dataclass
from pathlib import Path

import pyotp  # noqa: F401  (re-exported for the tests)
import requests
import urllib3
import websockets

urllib3.disable_warnings()

BASE = os.environ.get("E2E_BASE_URL", "https://localhost:1337").rstrip("/")
ROOT = Path(__file__).resolve().parents[1]
COMPOSE = shlex.split(
    os.environ.get("E2E_COMPOSE", "docker compose -f compose.yaml -f compose.dev.yaml")
)
PASSWORD = "E2e-Strong-Pass-9"

# Messages that are not app errors: headless Chromium without a GPU, and
# "Failed to load resource" repeats each 4xx answer (5xx are caught by status).
IGNORED_CONSOLE = ("GPU stall", "GL Driver Message", "WebGL", "Failed to load resource")

TLS = ssl.create_default_context()
TLS.check_hostname = False
TLS.verify_mode = ssl.CERT_NONE


def compose(*args, check=True):
    return subprocess.run([*COMPOSE, *args], cwd=ROOT, capture_output=True, text=True, check=check)


def sql(query):
    """One value from the database, through psql in the db container."""
    out = compose(
        "exec",
        "-T",
        "db",
        "sh",
        "-c",
        f'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc {shlex.quote(query)}',
    )
    return out.stdout.strip()


def tfa_secret(username):
    return sql(
        "select p.tfa_secret from api_profile p join auth_user u on u.id = p.user_id "
        f"where u.username = '{username}'"
    )


def next_code(totp):
    """A code from a time step not used yet (codes work once)."""
    step = totp.timecode(time.time())
    while totp.timecode(time.time()) == step:
        time.sleep(0.5)
    return totp.now()


@dataclass
class User:
    username: str
    email: str
    id: int
    uuid: str
    session: requests.Session

    @property
    def token(self):
        return self.session.cookies.get("access_token")

    def api(self, method, path, **kwargs):
        return self.session.request(method, BASE + path, **kwargs)

    def login_context(self, context):
        """Give a browser context this user's session cookie."""
        host = BASE.split("//", 1)[1].split(":")[0]
        context.add_cookies(
            [
                {
                    "name": "access_token",
                    "value": self.token,
                    "domain": host,
                    "path": "/",
                    "secure": BASE.startswith("https"),
                    "httpOnly": True,
                    "sameSite": "Lax",
                }
            ]
        )
        return context


def register(setup=True, prefix="e"):
    """New account through the API, logged in, profile set up by default."""
    name = prefix + secrets.token_hex(4)
    s = requests.Session()
    s.verify = False
    r = s.post(
        f"{BASE}/api/auth/register/",
        json={
            "username": name,
            "email": f"{name}@e2e.test",
            "password": PASSWORD,
            "confirm_password": PASSWORD,
            "first_name": "E",
            "last_name": "Two",
        },
    )
    assert r.ok, r.text
    r = s.post(f"{BASE}/api/auth/login/", json={"username": name, "password": PASSWORD})
    assert r.ok, r.text
    if setup:
        r = s.post(f"{BASE}/api/auth/setup/", data={"username": name})
        assert r.ok, r.text
    me = s.get(f"{BASE}/api/auth/me/").json()["data"]["user"]
    return User(name, f"{name}@e2e.test", me["id"], me["profile"]["uuid"], s)


def befriend(a, b):
    assert a.api("POST", "/api/friends/send/", json={"target_user": b.id}).ok
    assert b.api("POST", "/api/friends/accept/", json={"source_user": a.id}).ok


def ws_connect(path, user):
    return websockets.connect(
        BASE.replace("http", "ws", 1) + path,
        ssl=TLS if BASE.startswith("https") else None,
        additional_headers={"Cookie": f"access_token={user.token}", "Origin": BASE},
    )


class PageErrors(list):
    """Console errors, uncaught exceptions and failed requests of a page."""

    def watch(self, page):
        page.on("pageerror", lambda e: self.append(f"pageerror: {e}"))
        page.on("console", self._console)
        page.on("requestfailed", lambda r: self._failed(r))
        page.on("response", lambda r: r.status >= 500 and self.append(f"HTTP {r.status} {r.url}"))
        return page

    def _console(self, msg):
        if msg.type == "error" and not any(s in msg.text for s in IGNORED_CONSOLE):
            self.append(f"console.error: {msg.text[:300]}")

    def _failed(self, request):
        # Navigating away cancels pending requests: not an error.
        if request.failure and "ERR_ABORTED" not in request.failure:
            self.append(f"requestfailed: {request.url} {request.failure}")


class Sockets:
    """WebSockets opened by a page, seen from the browser."""

    def __init__(self, page):
        self.all = []
        page.on("websocket", lambda ws: self.all.append(ws))

    def open(self, path):
        return [ws for ws in self.all if ws.url.endswith(path) and not ws.is_closed()]

    def opened(self, path):
        return [ws for ws in self.all if ws.url.endswith(path)]


def wait_until(check, timeout=30, interval=0.2, message="condition", page=None):
    """Poll `check`. Pass the page when the check reads Playwright state
    (websocket status, events): its sync API only processes events while
    Playwright is called, so a plain sleep would never see them change."""
    end = time.time() + timeout
    while time.time() < end:
        if check():
            return
        if page is not None:
            page.wait_for_timeout(interval * 1000)
        else:
            time.sleep(interval)
    raise AssertionError(f"timed out waiting for {message}")


def png(width=8, height=8, rgb=(200, 30, 30)):
    """A valid PNG image, for avatar uploads (no Pillow needed)."""

    def chunk(kind, data):
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    row = b"\x00" + bytes(rgb) * width
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(row * height))
        + chunk(b"IEND", b"")
    )


def run_async(coroutine):
    """asyncio.run in a thread: the Playwright sync API keeps an event loop
    running in the main thread, so asyncio.run cannot be called there."""
    result = {}

    def target():
        try:
            result["value"] = asyncio.run(coroutine)
        except BaseException as error:  # re-raised in the test thread
            result["error"] = error

    thread = threading.Thread(target=target)
    thread.start()
    thread.join()
    if "error" in result:
        raise result["error"]
    return result.get("value")


def new_context(browser, user=None):
    """A browser context like the `context` fixture, optionally logged in."""
    context = browser.new_context(
        base_url=BASE, ignore_https_errors=True, viewport={"width": 1366, "height": 800}
    )
    return user.login_context(context) if user else context


def nav_click(page, selector):
    """Click an entry of the user menu in the nav (it opens on hover)."""
    page.locator("main-nav .user").first.hover()
    page.locator(f"main-nav .dropdown-content {selector}").first.click()

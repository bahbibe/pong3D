# Phase 6: Frontend core and security

Scope: `frontend/static/js/router.js`, `API/API.js`, `helpers.js`, `ws/*`, `index.js`, `components/*`, `frontend/server.js`, `frontend/index.html`.

## XSS sinks (server data into `innerHTML`)

Usernames are not validated server-side (Phase 2), and chat content is free text, so each of these is stored XSS. Auth cookie is HttpOnly, but XSS can still call the API as the victim (e.g. change password without the current one).

| Location | Data | Severity |
|---|---|---|
| `components/ChatBox.js:128-130` | chat `content` (from other user) | critical |
| `components/ChatBox.js:93-106` | friend `username`, `avatar` (attribute) | high |
| `components/Friends.js:59-69` | friend `username`, `avatar` | high |
| `pages/SearchPage.js:32-43` | every matching user's `username`, `avatar` | high |
| `pages/RankingPage.js:31-38` | all users' `username`, `avatar` (leaderboard) | high |
| `pages/Home.js:38-45` | best players' `username`, `avatar` | high |
| `pages/ProfilePage.js:57,109-115,176-200,279-284` | friends, blocked users, game opponents, friend requesters | high |
| `components/Profile.js:21` | own username | low (self) |
| `helpers.js:21-23` | API error messages (DRF can echo input, e.g. invalid pk) | low |
| `components/ErrorToast.js:14`, `components/Notification.js:17` | message passed by caller | low |

Fix pattern: build nodes and set `textContent` / `img.src` (like `helpers.js:renderNotifications` already does), or add one `escapeHTML()` helper in `helpers.js` and use it in every template literal. Fixing the username validator server-side (Phase 2) is the second layer, not the fix.

## Other findings

| Location | Severity | Problem | Fix |
|---|---|---|---|
| `router.js:24-25` | high | `BASE_URL = "http://localhost:8000"`, `WSS_URL = "ws://localhost:8000"`. Frontend talks to Django directly over plain HTTP/WS, skipping nginx TLS. Only works on the dev machine. Cross-origin setup is the reason for the open CORS config (Phase 1). | Serve frontend from nginx and use same-origin: `BASE_URL = ""`, `WSS_URL = \`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}\``. Then CORS can be removed. |
| `frontend/index.html` | med | No Content-Security-Policy. `three` is loaded through the import map from jsdelivr without integrity (Bootstrap and Font Awesome have SRI). A CSP would block most of the XSS above. | Add CSP (`script-src 'self' cdn.jsdelivr.net`; no inline). Self-host `three` (it is already in `package.json`, but version 0.162 vs 0.170 in the import map). |
| `helpers.js:38-41` | med | `hideOverlay` uses `setInterval` instead of `setTimeout`. Each call adds a 100 ms interval that never stops, so after the first hide the overlay can never be shown again. | `setTimeout(..., 100)`. |
| `router.js:139-164` | med | `getUser()` (a `/me` request) runs on every navigation, including redirects inside `router()`. A failed fetch (network error, non-JSON 500) throws and leaves a blank page. | Cache the user after first load; refresh on login/logout/settings. Wrap in try/catch, show an error state. |
| `ws/FriendsStatus.js:5-10`, `ws/NotificationsSockets.js:5-10` | med | `const socket` is block-scoped inside the `if`, and later lines use bare `socket` / `notif_socket`. It works only because `window.socket` is an implicit global. No reconnect: if the socket drops, it reopens only on the next navigation. | Keep the socket in a module variable, add reconnect with backoff, close on logout (ProfilePage does close them). |
| `ws/NotificationsSockets.js:19-24` | low | Live notifications are pushed to `window.notifications` without dedup and never marked read (mark-as-read calls are commented out in `helpers.js:104-116`). The counter only grows until reload. | Wire `mark_as_read`. |
| `components/ChatBox.js:80` | critical (server side, see Phase 3) | Client sends `author`. Server must not trust it. | Send only `content`. |
| `components/ChatBox.js:138-152` | low | `receiveMessage` recurses through promises for every message (chain grows for the whole chat session). | Use `socket.onmessage` with a handler. |
| `components/Friends.js:16-28` | low | Clicked friend is found by matching username text in the DOM. | Store friendship uuid in `data-uuid`. |
| `router.js:39-132` | low | `view` field unused (only `page` is used); `/blocked`, `/tournament`, `/join` list wrong `view` classes. `pathToRegex` uses `(.+)`, which matches `/` too. | Remove `view` or use it; use `([^/]+)`. |
| `index.js:7-11` | low | `event.target.matches("[data-link]")` misses clicks on children of the link (icons, spans). | `event.target.closest("[data-link]")`. |
| `API/API.js` | low | Same 15-line fetch block copied 10 times; `getTournament` calls a non-existent `/get_participants/` route. Many pages bypass `API.js` and call `fetch` directly. | One `request(path, opts)` helper; delete dead methods; use it everywhere. |
| `server.js` | low | Express serves `index.html` for any path, no security headers, runs under nodemon. Not needed if nginx serves the static files. | Serve from nginx; drop Express in prod. |
| dead files | low | `pages/_FriendPage.js`, `pages/blockedFriends.js` (all commented), `API/help.js` (empty), `frontend/dataa.json` (mock data), `pages/tourPage.js`/`JoinPage.js` (routed to `ScorePage`?). | Delete or wire up. |

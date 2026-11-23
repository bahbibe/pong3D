# Phase 7: Frontend pages, game client, UX

Scope: `frontend/static/js/pages/*.js`, `frontend/static/css/*`, assets.

| Location | Severity | Problem | Fix |
|---|---|---|---|
| `pages/ProfilePage.js:162` | high | Fetches `${BASE_URL}/game/history/` (missing `/api`). Returns 404 HTML/JSON, then `data.data.stats` throws. Match history and stats on the profile page never load. | `/api/game/history/`. Check `response.ok` before reading `data.data`. |
| `pages/ProfilePage.js:176-200` | med | History rendering assumes both players exist. Tournament placeholder games have `null` players, so `game.player.username` throws and stops the loop. | Skip games without both players (or fix on server with a status filter, Phase 4). |
| `pages/GamePage.js:80-85,253` | med | Resize listener is an anonymous function, but cleanup removes `this.onResize` (undefined). After leaving the game page, each resize runs on a disposed page and throws (`this.camera` is null). | Store the handler: `this.onResize = () => {...}`, add/remove the same reference. |
| `pages/GamePage.js:141-142,254-255` | low | Keys bound with `document.onkeydown = ...` but removed with `removeEventListener`, which does not clear property handlers. | Use `addEventListener` in both places, or set `document.onkeydown = null`. |
| `pages/GamePage.js:74-147` | low | If the user leaves before the GLB finishes loading, the `.then` runs after `disconnectedCallback` nulled `scene`/`renderer` and throws. | Set a `this.disposed` flag and return early in the promise chain. |
| `pages/GamePage.js:89-93` | low | `console.log` twice per server message (60/s). Slows the game, floods the console. | Remove. |
| `pages/GamePage.js:198-203` | low | `updateScore` creates new canvas textures without disposing the old ones (GPU memory leak per point). | `material.map?.dispose()` before replacing. |
| `pages/GamePage.js:161-177` | med | Keyboard only (arrow keys via deprecated `keyCode`). No touch controls, yet the README claims the "Support on all devices" module. Game is not playable on phones/tablets. | Add on-screen left/right buttons or touch drag; use `e.key === "ArrowLeft"`. |
| `pages/GamePage.js:45-48` | low | `/play` (no id) builds `ws/game/undefined`. | Redirect `/play` to matchmaking or bot. |
| `pages/MatchmakingPage.js:31-36` | low | `if` without braces: only the first line is conditional. Loader hides and navigation happens on any message. | Add braces. |
| `pages/ScorePage.js:17-28` | low | Bot game score page shows scores from the URL query (client-controlled). Display only, no harm, but easy to fake. | Fine for bot games; document. |
| `pages/SearchPage.js:16,25` | low | Query read from `localStorage` (persists across sessions) and put in the URL without `encodeURIComponent` (`&`, `#`, `%` break search). | Pass query in the route (`/search?q=`), encode it. |
| `pages/Settings.js` vs `pages/SetupPage.js` | low | Near-identical files (avatar upload, 2FA enable/confirm/disable). Fixes must be done twice. | Extract shared 2FA/avatar component. |
| `pages/friendPage.js`, `ProfilePage.js` | low | Each page does its own `fetch` with copied error handling, not `API.js`. | Use `API.js`. |
| `static/asset/images/*.JPG` | low | 8.5 MB of assets, including team photos (`bahbibe.JPG`, `abeihaqi.JPG`, `mahansal.JPG`, ~160 KB+ each) served at full size. | Resize/compress to WebP, lazy-load. |
| `static/css/index.css` | low | 1094 lines, one file, plus `style.css`. Not reviewed line by line; no obvious issues from a scan. | Optional cleanup. |
| general | low | No accessibility work: icon-only buttons have no `aria-label`, toast/notifications not announced, game has no non-visual feedback. Not claimed in README, so info only. | - |

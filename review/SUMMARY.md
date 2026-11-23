# Code review summary: pong3D

Seven phase reports in this folder. This file is the triage for Phase 8 (fixes).
Counts are approximate: critical 7, high ~25, med ~40, low ~60.

## Fix batches (in order)

Each batch = one branch commit, with tests where the guard is testable.

### Batch 1: Account takeover chain (critical)
1. 2FA bypass: unverified token may only call `twofa/verify/`; `disable_twofa` requires a code. (`api/auth_utils.py`, `auth_views.py`)
2. Chat: server builds message from `scope["user"]`; validate content; membership + block check on WS and REST. (`chat/consumers.py`, `chat/views.py`)
3. Frontend XSS: escape helper / `textContent` in every sink listed in Phase 6.
4. Username validator + `validate_password` in serializers. (`api/serializers.py`)
5. `settings/update/` requires current password for password/email change.
Tests: APIClient tests for 2FA allowlist and disable; WebsocketCommunicator tests for chat spoofing, non-member, blocked user.

### Batch 2: Config and cross-origin (critical/high)
1. `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` from env; restrict CORS to the frontend origin (or same-origin via nginx and drop CORS).
2. Cookie `secure=True, samesite="Lax"` in one helper.
3. `.dockerignore` inside the backend build context; stop publishing adminer/grafana/prometheus/8000.
4. Frontend `BASE_URL`/`WSS_URL` same-origin; nginx serves frontend + avatars.
Test: `manage.py check --deploy`.

### Batch 3: Game correctness (critical/high)
1. Matchmaking `opponent_id[0]` -> `int(opponent_id)`.
2. `GameInstance.game_loop` group name bug (`self.player`); log task exceptions.
3. Stop and cancel game/bot tasks on end/abandon; fix str/int bot key.
4. Server-side paddle speed (direction state, fixed step per tick).
5. Save game only on score change, `update_fields`.
6. Remove dead `game_update` branch; validate WS input; auth checks on all consumers.
Tests: consumer tests for matchmaking with user id >= 10, anonymous rejection, task cancelled after disconnect.

### Batch 4: Friends/state rules (high)
1. `accept_friend_request` requires pending; restrict or remove `update_friendship_status`.
2. Intra login by `intra_id` only.
3. Rate limit login and 2FA verify.
4. GET -> POST for `create_tournament`, `invite_friend`, `play_again`.
Tests: block escape attempts, forced friendship, intra username collision.

### Batch 5: Data model (high/med, needs migrations)
1. `Game.status/winner/created_at`; stats only on finished games.
2. Replace `DO_NOTHING` FKs.
3. Profile auto-create signal + atomic register.
4. Remove `makemigrations` from entrypoint; switch to daphne; fix `asgi.py` import order.

### Batch 6: Med/low cleanup
Everything else in the phase reports (N+1 queries, async redis, dead files, frontend listener leaks, ProfilePage `/api` path, `hideOverlay`, etc.). Can become GitHub issues instead of commits.

## Not verified
- Runtime behaviour: nothing was run (no Django/yarn/pip-audit installed locally). The `GameInstance` crash and the leaderboard `ImageFieldFile` issue are from reading the code; confirm in the container.
- Dependency CVEs: run `pip-audit` and `yarn audit`.
- `makemigrations --check` drift.

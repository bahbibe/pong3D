# Phase 5: Data model and migrations

Scope: all `models.py` and `migrations/` in `backend/backend/`.

Could not run `makemigrations --check` here (Django not installed locally). Run it in the container before Phase 8.

| Location | Severity | Problem | Fix |
|---|---|---|---|
| `game/models.py:8-9,17,21,29-30` | high | FKs use `on_delete=models.DO_NOTHING` (`Game.player1/2`, `Tournament.owner`, `Tournament_Participants.player`, `Tournament_Game.tournament/game`). Postgres FK constraints are still created, so deleting a user or tournament fails with `IntegrityError`. Account deletion (GDPR module) cannot work. | `SET_NULL` for players/owner (fields are already nullable or make them so), `CASCADE` for `Tournament_Game.tournament`. |
| `game/models.py:6-12` | high | `Game` has no state, winner or timestamps (see Phase 4). Stats cannot tell played from unplayed games. | Add `status`, `winner` (FK, null), `created_at`, `finished_at`. Data migration: mark existing games with a score of 11 as finished. |
| `api/models.py:8-24` + `auth_views.py:113-120,229-243` | med | `Profile` is created by hand in two places, with no transaction and no signal. A user created another way (admin, `createsuperuser`) has no profile, and every `user.profile` access raises `RelatedObjectDoesNotExist`. | `post_save` signal on `User` with `get_or_create`, or create inside `transaction.atomic()` everywhere. Data migration to backfill. |
| `api/models.py` (User) | med | Email is not unique at DB level, but the app treats it as a login key (`login_user` uses `.filter(email=...).first()`). Duplicates make login pick an arbitrary account. | Unique constraint on `lower(email)` (via Profile or a custom check), after deduplicating. |
| `api/models.py:16` | med | `intra_id` not unique and not indexed. Two profiles with the same intra id break the intra login lookup. | `unique=True, null=True`. |
| `friends/models.py:27-28` | med | `unique_together(source_user, target_user)` does not stop the reverse pair (B->A next to A->B). | `UniqueConstraint(Least("source_user", "target_user"), Greatest(...), name=...)`, or always store lower id first. |
| `chat/models.py:12` | med | `Message.conversation` is a free `CharField(null=True)` holding the friendship uuid. No FK, no index; history query scans the table. Deleting a friendship leaves orphan messages. | `ForeignKey(Friendship, on_delete=CASCADE)` or at least `db_index=True`. |
| `api/models.py:31-38` | low | `Notification.user` has `related_name="user"` and `sender` has `related_name="sender"`. So `user.user` is the user's notifications. Confusing. `game_id` is `CharField(null=True)` with no `max_length` and holds either `"<id>"` or `"<tournament_uuid>/<id>"`. | `related_name="notifications"` / `"sent_notifications"`. Split `game` FK and `tournament` FK. |
| `api/models.py:20-21` | low | `Profile.total_wins/total_losses` are never updated but are returned by `ProfileSerializer` (always 0). Stats are computed from games. | Drop the fields, or update them at game end and stop recomputing. |
| `api/migrations/0005-0007` | low | `Freindship` model (typo) created, changed, then deleted in the `api` app. Moved to `friends`. | Squash api migrations (`squashmigrations api 0001 0014`) once all environments are migrated. |
| `chat/migrations/0001-0008` | low | 8 migrations for one model, including a second `initial = True` (`0004_initial`) after deleting all models in `0003`. | Squash, or reset chat migrations (dev data only). |
| `game/migrations/0002-0009` | low | `unique_together` changed 3 times, `t_round` moved between models. | Squash. |
| `backend/backend/entrypoint.sh` | high | (dup of Phase 1) `makemigrations` at boot can create migrations that are not in git, so environments drift. | Remove; add `makemigrations --check --dry-run` in CI. |

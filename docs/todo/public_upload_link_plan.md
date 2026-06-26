# Public Upload Links (inbound file/folder drop)

## Context

Today `gws_core` only supports **outbound** sharing: an authenticated user generates a public link so external people can *download* an existing resource (the `gws_core/share/` module — `ShareLink` model, `share_controller`, `ShareTokenAuth`). There is no way to let an external, unauthenticated person *send files in*.

This feature adds the inverse: a lab user generates a **unique public URL** that anyone with the link can use to **upload a file or a folder** into the lab. The link is configurable (expiration, max number of files, allow folder, allowed extensions, per-file max size, max total size, label) and **secured by an unguessable token in the URL** — possessing the full URL is the credential (no separate code).

Each received upload becomes a new `File`/`Folder` `ResourceModel` owned by the link's creator, reusing the existing `FsNodeService` upload pipeline. **Scope: backend only** — the external upload page lives in the separate `lab-front` repo and is out of scope here; this plan delivers the model + config + secured public API that lab-front (or any client) calls.

## Design overview

A new self-contained module `src/gws_core/share/upload_link/` (mirrors the structure of the existing `share/` module: model + service + two controllers + DTOs). It is *not* folded into `ShareLink` because that model is entity-bound (points at an existing resource) whereas an upload link has no target entity yet and carries upload-specific config.

### URL shape (token only — no code)
```
{lab_api_url}/{core_api}/upload-link/{token}            # GET  -> link info (config, validity)
{lab_api_url}/{core_api}/upload-link/{token}/file       # POST -> upload one file
{lab_api_url}/{core_api}/upload-link/{token}/folder     # POST -> upload a folder
{lab_api_url}/{core_api}/upload-link/{token}/uploaded   # GET  -> files already uploaded via this token
```
- `token` = unguessable id (UUID + timestamp, same recipe as `ShareLinkService` line 66-68). This is the only secret.
- The token must match an active, non-expired link, or the request is rejected with a generic "invalid link" error.

## Files to create

### 1. `src/gws_core/share/upload_link/upload_link.py` — Peewee model
`class UploadLink(ModelWithUser)` (base gives `id`, `created_at`, `created_by`, `last_modified_by`; see `core/model/model_with_user.py`). Fields (use `typed_db_field` types as in `share_link.py`):
- `token = TypedCharField(max_length=100, unique=True)` — the only secret
- `label = TypedCharField(null=True)` — human description
- `valid_until = NullableDateTimeUTC()` — expiration (null = never)
- `max_file_count = TypedIntegerField(null=True)` — null = unlimited
- `uploaded_count = TypedIntegerField(default=0)` — incremented per successful upload
- `allow_folder = TypedBooleanField(default=False)`
- `max_file_size = TypedIntegerField(null=True)` — per-file byte cap, null = no cap
- `max_total_size = TypedIntegerField(null=True)` — **cumulative** byte cap across all uploads on this link, null = no cap
- `uploaded_size = TypedIntegerField(default=0)` — running total of bytes received, incremented per successful upload
- `allowed_extensions = TypedJSONField(null=True)` — list[str] like `["csv","pdf"]`, null/empty = any
- `is_active = TypedBooleanField(default=True)` — manual disable (separate from expiration)

Methods (mirror `ShareLink`):
- `is_valid() -> bool`: `is_active and (valid_until is None or valid_until > DateHelper.now_utc())`
- `check_can_upload(file_count: int, incoming_size: int)`: raises `BadRequestException` if expired/disabled, if `max_file_count` would be exceeded by `uploaded_count + file_count`, or if `max_total_size` would be exceeded by `uploaded_size + incoming_size`. **Limit-reached behavior: reject the new upload but keep the link** (no auto-disable).
- `check_extension(filename)` / `check_size(size)`: validate each file against `allowed_extensions` / `max_file_size`.
- `get_upload_url() -> str`: `{Settings.get_lab_api_url()}/{Settings.core_api_route_path()}/upload-link/{token}` (the shareable secret URL).
- `to_dto()` -> `UploadLinkDTO`.
- `Meta`: `table_name = "gws_upload_link"`, `is_table = True`.

### 2. `src/gws_core/share/upload_link/upload_link_dto.py` — DTOs (`BaseModelDTO`)
- `GenerateUploadLinkDTO` (creation request): `label`, `valid_until`, `max_file_count`, `allow_folder`, `max_file_size`, `max_total_size`, `allowed_extensions`.
- `UpdateUploadLinkDTO`: same fields + `is_active`.
- `UploadLinkDTO` (response, incl. audit fields, `upload_url`, `uploaded_count`, `uploaded_size`).
- `PublicUploadLinkInfoDTO` (what the anonymous page gets — config needed to render the form: `label`, `allow_folder`, `allowed_extensions`, `max_file_size`, `max_total_size`, `max_file_count`, remaining file count, remaining bytes, `valid_until`; **never** leak `created_by`/internal ids).
- `UploadedFileDTO` (one already-uploaded item, safe for anonymous eyes): `name`, `size`, `uploaded_at` only — **no** resource id, no owner, no internal `ResourceModelDTO`.

### 3. `src/gws_core/share/upload_link/upload_link_service.py` — business logic
Mirror `ShareLinkService`. Methods:
- `generate_upload_link(dto) -> UploadLink`: build model, set `token` (UUID+ts), save. `created_by` auto-set by `ModelWithUser._before_insert`.
- `find_by_token_and_check(token) -> UploadLink`: `get_or_none(token=token)`; raise generic `BadRequestException("Invalid upload link")` if missing or `not is_valid()`. (Mirrors `ShareLink.find_by_token_and_check`.)
- `receive_file(token, upload_file, typing_name)`: validate link → `check_can_upload(1, size)` + extension/size checks → **establish creator user context** (see Auth note) → call `FsNodeService.upload_file(upload_file, typing_name)` (`impl/file/fs_node_service.py:71`) → **tag the resulting `ResourceModel`** (see Tagging) → increment & save `uploaded_count` + `uploaded_size` → return `ResourceModel`.
- `receive_folder(token, files, folder_typing_name)`: same, gated on `allow_folder`, calls `FsNodeService.upload_folder` (`fs_node_service.py:121`), tags the result. Counts as 1 upload unit toward `max_file_count`; its total bytes count toward `max_total_size`.
- `get_uploaded_resources(link_id) -> list[ResourceModel]`: **tag-based retrieval** — `TagService.get_entities_by_tag(TagEntityType.RESOURCE, Tag(TagSystem.UPLOAD_LINK_TAG_KEY, link_id))` (`tag/tag_service.py:261`). Used by the authenticated creator route.
- `get_uploaded_files_public(token) -> list[UploadedFileDTO]`: validate token → `get_uploaded_resources(link.id)` → project each to the **safe** `UploadedFileDTO` (name/size/uploaded_at only). Used by the anonymous `/uploaded` route so an external user can see what they've already sent.
- `update_upload_link`, `delete_upload_link`, `get_upload_links` (paginated, like `ShareLinkService.get_shared_links`).
- Wrap receive methods in `@GwsCoreDbManager.transaction()` so the resource save + tag + counter bumps are atomic.

#### Tagging uploaded resources (for retrieval)
First, **register the reserved tag key in `TagSystem`** (`tag/tag_system.py`) — that class centralizes all system tag keys; do not hard-code the string:
```python
# Tag to identify resources uploaded through a public upload link.
# Value is the id of the UploadLink.
UPLOAD_LINK_TAG_KEY = "gws_upload_link_id"
```
Then, right after a resource is created in a `receive_*` call, attach the tag identifying its source link:
```python
TagService.add_tag_to_entity(
    TagEntityType.RESOURCE, resource_model.id, Tag(TagSystem.UPLOAD_LINK_TAG_KEY, link.id)
)
```
- Tag value = the `UploadLink.id`. (`tag/tag_service.py:269`, `Tag` at `tag/tag.py:195`.)
- Retrieval is then a single `TagService.get_entities_by_tag(TagEntityType.RESOURCE, Tag(TagSystem.UPLOAD_LINK_TAG_KEY, link_id))` call — no extra join column needed on `ResourceModel`.

### 4. `src/gws_core/share/upload_link/upload_link_controller.py` — authenticated management routes
Registered on `core_app` (`from gws_core.core_controller import core_app`), each guarded by `_=Depends(AuthorizationService.check_user_access_token)` (pattern: `fs_node_controller.py:23`):
- `POST /upload-link` (create) → `UploadLinkDTO`
- `GET  /upload-link` (list, paginated) → `PageDTO[UploadLinkDTO]`
- `PUT  /upload-link/{id_}` (update config / activate-deactivate)
- `DELETE /upload-link/{id_}`
- `GET  /upload-link/{id_}/resources` → `list[ResourceModelDTO]` — resources uploaded through this link, via `get_uploaded_resources` (tag lookup).

### 5. `src/gws_core/share/upload_link/upload_link_public_controller.py` — anonymous public routes
**No `check_user_access_token` dependency** (security is the token in the path — same philosophy as the existing public `preview_a_file` route at `fs_node_controller.py:65-84`):
- `GET  /upload-link/{token}` → `PublicUploadLinkInfoDTO` (lets the page validate the URL up-front & render config: max files, max sizes, allowed extensions, remaining quota). Calls `find_by_token_and_check`.
- `POST /upload-link/{token}/file` (`UploadFile = FastAPIFile(...)`, `typing_name`) → minimal confirmation DTO (e.g. `{filename, success}`) — **do not** return internal `ResourceModelDTO` to anonymous callers.
- `POST /upload-link/{token}/folder` (`list[UploadFile]`, `folder_typing_name`) → confirmation DTO.
- `GET  /upload-link/{token}/uploaded` → `list[UploadedFileDTO]` — lets the anonymous uploader see which files they've already uploaded through this link (safe projection only).

> **Table creation:** no migration needed — declaring the model with `Meta.is_table = True` (like `share_link.py:181-184`) auto-creates `gws_upload_link`. The new `UPLOAD_LINK_TAG_KEY` reuses the existing `gws_entity_tag` table, so no schema change there either.

## Wiring / registration
- Import the two new controllers wherever brick controllers are loaded so their `@core_app` routes register at import time. **Find where `share_controller` / `fs_node_controller` get imported** (grep for `share_controller` import in the controller-loading module, likely a `_controllers.py` or the brick's app init) and add the two new controller modules alongside.
- The model auto-registers its table via `Meta.is_table = True` (verify against how `share_link.py` is handled — no explicit table list / migration required).

## Auth note (important, verify during implementation)
Uploaded resources are persisted via `ResourceModel.save_from_resource(...)` whose `created_by` comes from `CurrentUserService.get_and_check_current_user()`. On an **anonymous** route there is no current user, so the service must set one before calling `FsNodeService`. Two viable options, in order of preference:
1. Reuse the existing pattern: build an `AuthContextShareLink`-equivalent and `CurrentUserService.set_auth_context(...)` with **the link's `created_by` user** (so uploads are owned by the link creator — matches the chosen "New Resource per upload, owned by creator" behavior). See `authorization_service.py:182-184` and `share_controller.py:38` (`share_link.created_by`).
2. Fallback to `User.get_and_check_sysuser()` (what public share links use, `authorization_service.py:180`) if owning-as-creator proves awkward.
Confirm which `CurrentUserService` setter to call and whether a context-reset is needed after the request.

## Reuse summary (don't re-implement)
- Upload pipeline: `FsNodeService.upload_file` / `upload_folder` — `impl/file/fs_node_service.py:71,121`.
- Token recipe (the only secret): `StringHelper.generate_uuid()` + `DateHelper.now_utc_as_milliseconds()` — `share_link_service.py:66-68`.
- Token lookup precedent: `ShareLink.find_by_token_and_check` — `share_link.py:31`.
- Model base + audit fields: `ModelWithUser` — `core/model/model_with_user.py`.
- Typed fields: `core/model/typed_db_field.py`.
- Public-route precedent: `fs_node_controller.py:65-84` (`preview_a_file`).
- Expiry helpers: `DateHelper.now_utc()` / `is_valid()` — `share_link.py:146`.
- Tagging + tag-based retrieval: `TagService.add_tag_to_entity` (`tag/tag_service.py:269`), `TagService.get_entities_by_tag` (`tag/tag_service.py:261`), `Tag` (`tag/tag.py:195`), `TagEntityType.RESOURCE`. Reserved tag key registered in `TagSystem` (`tag/tag_system.py`).
- Auto-created table via `Meta.is_table = True` (`share_link.py:181-184`) — no migration.

## Verification
1. **Tests** — add `tests/test_gws_core/.../test_upload_link.py` (run `cd bricks/gws_core && gws server test test_upload_link`). Cover:
   - create link → returns token+url; `find_by_token_and_check` finds it.
   - public `GET /upload-link/{token}` returns config; unknown token → `BadRequestException`.
   - upload file via public route → new `ResourceModel` exists, `uploaded_count == 1`, owned by creator.
   - `max_file_count` reached → next upload rejected, link still present (not disabled).
   - `max_total_size` reached → next upload rejected (cumulative byte cap).
   - expired / `is_active=False` link → upload rejected.
   - `allow_folder=False` → folder route rejected; `allowed_extensions` / `max_file_size` enforcement.
   - upload 2 files → `get_uploaded_resources(link_id)` (and `GET /upload-link/{id}/resources`) returns exactly those 2, each carrying the `upload_link` tag.
   - public `GET /upload-link/{token}/uploaded` returns the 2 files as `UploadedFileDTO` (name/size only, no resource ids/owner leaked).
2. **Manual smoke** — `gws server run`, create a link via the authenticated `POST /upload-link`, then `curl -F file=@some.csv` the returned public `.../file` URL and confirm the resource appears.
3. `ruff check --fix` on all new/modified files.

## Size measurement note
`max_file_size` / `max_total_size` need the byte count of each incoming file. FastAPI's `UploadFile` exposes `.size` for spooled uploads, but it can be `None`; the robust path is to measure after the temp file is written (`FileHelper`/`os.path.getsize` on the temp path that `FsNodeService.create_tmp_file` produces) and roll back the transaction if a cap is exceeded. Decide whether to pre-check (reject before writing, using `UploadFile.size` when available) or post-check (write to temp, measure, reject+rollback) — post-check is simpler and the transaction wrapper makes it safe.

## Open items to confirm during implementation
- Where controllers are imported/registered (grep `share_controller`).
- Folder counting rule toward `max_file_count` (proposed: 1 folder = 1 unit).
- Whether anonymous resources should be owned by creator (preferred) vs sysuser.

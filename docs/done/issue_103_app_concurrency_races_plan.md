# Fix issue #103 — concurrency races in app startup + logging gaps

## Context

[Issue #103](https://github.com/Constellab/gws_core/issues/103) documents three races with the same shape (N concurrent writers, one shared mutable directory/file, no lock, no atomic swap) plus logging gaps that made diagnosis hard:

1. **Plugin install race** — every app instance + granian worker installs `reflex-components` into the shared `<app_folder>/assets/external/gws_plugin` at import time, while `clear_app_cache()` deletes it. Silent-corruption path: a losing unzip can leave a partial tree with a valid `version.json`, which `install_package()` trusts forever.
2. **Reflex build race (dominant failure — 36 failed starts in one day)** — N concurrent `reflex export` runs in one shared app folder destroy each other's `.web`/`node_modules`.
3. **nginx config race** — `_generate_nginx_config()` truncate-writes the live `nginx.conf` from concurrent threads; nginx reads a prefix (`pread() returned only N bytes`, `no "events" section`).
4. **Logging gaps** — MAIN records carry no `context_id`, subprocess output is unattributed, stderr is logged ERROR regardless of exit code, no build start/end records.

Decisions confirmed:
- All four workstreams in scope, as separate commits.
- Plugin materialized into each app folder by **plain copy** (not symlink) from an immutable shared store.
- **Part B** (same-origin routing + shared build cache so N instances need only 1 build) ships as a **second PR** after the race fixes — it changes URL topology for every prod Reflex app and needs runtime verification.

Verified up front: `zip_compress.py` on main is already hardened (stderr capture + integrity pre-check) — no change needed. "Error processing write queue" is vendored Reflex code — not fixable here.

---

# PART A — Race fixes + logging (PR 1)

## A1. Plugin install: version-keyed immutable store, atomic install, copy materialization

**Files:** `src/gws_core/apps/app_plugin_downloader.py`, `src/gws_core/apps/reflex/_gws_reflex/gws_reflex_main/reflex_plugin.py`, `src/gws_core/apps/reflex/_gws_reflex/gws_reflex_main/gws_components/__init__.py`, `src/gws_core/apps/streamlit/streamlit_plugin.py` (adapt), `src/gws_core/apps/reflex/reflex_process.py`

### Store layout and atomic install (`AppPluginDownloader`)
- Install into `<brick-data>/gws_core/<package_name>/<DASHBOARD_COMPONENTS_VERSION>/` — the existing dead-code `get_version_folder_path()` (app_plugin_downloader.py:100-106) becomes the real content path. Version in the path ⇒ directory is immutable once complete; a new version is a new directory.
- **Atomic fill:** download zip to a temp file, unzip into `<store>/<version>.tmp.<pid>` (same filesystem), run `post_install()` (writes `environment.json` — built only from `Settings` classmethods + a constant base href, so it is lab-wide and belongs in the store), verify (`version.json` content == `DASHBOARD_COMPONENTS_VERSION`, `index.html`, `assets/` present), then `os.replace()` to the final path. If the rename fails with `OSError`/`ENOTEMPTY` (someone else won) → delete own tmp, use the existing dir. "Exists" now means "complete" — kills the silent-corruption path.
- **`fcntl.flock` dedupe** (stdlib, no new dependency — none exists in the codebase today): lock `<store>/<version>.lock` across check-then-install so concurrent installers don't all download. Layered on top of atomicity, never instead of it.
- Stop using `FileDownloader.download_file_if_missing`'s existence check as an install marker (`file_downloader.py:63-65` treats any partial dir as "already downloaded") — download to a temp location explicitly.
- **New `materialize(dest_path)` method:** if `dest/version.json` matches the store version → skip; else copy store dir to `<dest_parent>/.tmp.<pid>` and `os.replace()` onto dest (delete stale dest first if replace hits ENOTEMPTY, then re-check version — the source being immutable makes any winner correct).
- Dev mode: `_install_from_local_folder()` (line 186) switches from `shutil.move` to copy (the move consumes the source, so it cannot feed a shared store).
- Delete stale version dirs of the same package after a successful install (simple GC).

### ReflexPlugin + import-time install
- `ReflexPlugin` drops its cwd destination override (`reflex_plugin.py:33-45`); it installs to the shared store and exposes `materialize_into_app(app_folder)` → copy into `<app_folder>/assets/external/gws_plugin`.
- `ReflexProcess` calls install + materialize explicitly **before** launching build (prod, inside the A2 build lock, after `clear_app_cache()`) and before `reflex run` (dev).
- `gws_components/__init__.py::__load_plugins__()` (line 47-56) becomes **verify + self-heal**: if the materialized folder matches the store version → no-op; if missing/stale → materialize from the store (safe now: immutable source, atomic copy, flock-guarded install). No more 2.2 MB downloads from inside granian worker imports in the normal path.
- `CACHE_FOLDER_NAMES` keeps `assets/external` (fix (e) from the issue is unnecessary with the copy approach): the clear + re-copy both happen under the A2 build lock, giving the folder a single owner.

### StreamlitPlugin
- Same base-class benefits: install to shared store, then `materialize()` into the streamlit package `static/gws_plugin` dir (its current destination override becomes a materialization target). Behavior otherwise unchanged.

## A2. Reflex build serialization (the dominant failure)

**Files:** `src/gws_core/apps/reflex/reflex_process.py`, small new helper (e.g. `src/gws_core/apps/app_dir_locks.py`)

- Module-level registry `dict[str, threading.RLock]` keyed by canonical app-folder path, guarded by a global lock (`get_app_folder_lock(path)`). Threads-in-one-process is confirmed (`app_process.py:201` spawns `Thread` per start; there is exactly one FastAPI server process), so `threading` locks suffice; document why (and when flock would become necessary).
- `_build_frontend()` (reflex_process.py:179):
  1. Acquire the app-folder lock.
  2. **Re-check `get_front_build_path_if_exists()` inside the lock** (double-checked locking — today's check at line 182 races).
  3. If present → release, reuse.
  4. Else `clear_app_cache()` → materialize plugin (A1) → `reflex export` → unzip to the per-resource build folder → `update_front_build_info()`, all while holding the lock.
- Note in code/PR: builds for N *distinct* resources of the same app remain N sequential builds in Part A (build output folder is per-resource, `reflex_resource.py:92-109`); Part B collapses them to 1.
- Also fix the unlocked `_get_cached_reflex_access_token` class-level TTL cache (reflex_process.py:50-52, 335-373) with a small lock — same check-then-set shape, found during exploration.
- Keep `clear_app_cache()` on every build for now (its corruption rationale largely disappears with serialization, but skipping it interacts with reflex version bumps — revisit after Part B makes builds rare).

## A3. nginx: atomic write + serialized generate-then-reload

**File:** `src/gws_core/apps/app_nginx_manager.py`

- `_generate_nginx_config()` (line 209): write to `nginx.conf.tmp.<pid>.<tid>` in the same dir, then `os.replace()` onto `nginx.conf`. Readers see whole-old or whole-new, never a prefix — eliminates all three `[emerg]` variants.
- One class-level `threading.RLock` (RLock because `start_or_reload()` → `nginx_is_running()` → `stop(force=True)` can nest, line 197) held across: `register_services`/`unregister_services` dict mutation + `_generate_nginx_config()` + `_reload_nginx()`/`_start_nginx()`, and in `stop()`. The reloaded config is the config just generated; also closes the `nginx_is_running()`→`_start_nginx()` TOCTOU.
- Make `get_instance()` (line 99) thread-safe; register the `atexit` stop hook once (today it stacks per start, line 158).
- `_run_nginx_command`: for these short commands, capture stdout+stderr and log **by exit code**: success → DEBUG/INFO, failure → one ERROR containing the exit code *and* nginx's stderr (today "Failed to reload nginx configuration" carries neither, and successful `nginx -t` output lands at ERROR — logging item 3 for nginx).
- No debounce in this PR (issue marks it optional; self-healing once writes are atomic). Note as follow-up.

## A4. Logging improvements

**Files:** `src/gws_core/core/utils/logger.py`, new `src/gws_core/core/utils/app_log_context.py` (mirror of `request_context.py`), `src/gws_core/impl/shell/shell_proxy.py`, `src/gws_core/core/classes/observer/message_dispatcher.py`, `src/gws_core/core/classes/observer/message_observer.py`, `src/gws_core/apps/app_process.py`, `src/gws_core/apps/apps_manager.py`, `src/gws_core/apps/reflex/reflex_process.py`

1. **`context_id` on MAIN records (item 1, highest impact).**
   - New `ContextVar`-based `AppLogContext` (set/get/clear + context manager), following the existing `request_id` precedent (`request_context.py`, read in `JSONFormatter.format` at logger.py:62).
   - `JSONFormatter.format`: `context_id = self.context_id or AppLogContext.get()`.
   - Set it at the app-operation entry points: `AppProcess._start_app_and_watch` (thread entry — covers build, plugin install, nginx registration), `stop_process`, `update_custom_subdomain`.
   - Thread propagation: `ContextVar`s don't cross `Thread` boundaries — `ShellProxy.run_in_new_thread`'s output-reader thread must run its target under `contextvars.copy_context()`; `MessageDispatcher` must stamp each message with the current `context_id` at `notify_message` time (messages are flushed later from a `Timer` thread) and `LoggerMessageObserver` passes it to `Logger` via `extra` (extend `Logger.info/debug/warning` to accept `extra` like `error` already does for `instance_id`).
   - Consumer side: `AppsManager.get_logs_of_app` (apps_manager.py:546-579) additionally matches MAIN records whose `context_id` equals the app id, so build/nginx/plugin logs become visible in the app's log view.
2. **Build start/end records (item 4).** In `_build_frontend`: paired `Logger.info` "Frontend build started/finished for app <resource_id>" with elapsed seconds (and "failed after Xs" on the raise path).
3. **Subprocess output attribution (item 2).** `ShellProxy`: log the PID in `run_in_new_thread` (missing today, unlike `run`); tag dispatched stdout/stderr lines with `[pid <pid>]` (store pid at popen; the per-proxy dispatcher means merged lines share one pid).
4. **stderr level (item 3).** `_self_dispatch_stderr` (shell_proxy.py:448) downgrades streamed stderr from unconditional ERROR to WARNING; the exit-code summary becomes the ERROR: "[ShellProxy] Command failed (exit N)". nginx commands handled in A3. (Fixes reflex's deprecation warnings and `nginx -t` success being logged as ERROR, while real failures still produce an ERROR with the code.)
5. **Traceback pairing (item 5, cheap part).** `app_process.py:238`: `Logger.error(..., exception=e)` so "Error while starting app <id>" carries its stack trace in one record.

Also guard `MessageDispatcher._waiting_messages` / `_running_dispatch_timers` with a lock — `_running_dispatch_timers` is currently a *class* attribute mutated per-instance without one (message_dispatcher.py:46) — found during exploration, same defect family.

## A5. Tests (Part A)

New test files under `tests/test_gws_core/apps/` (none exist today for these):
- `test_app_plugin_downloader.py` — atomic install (tmp+replace), concurrent installs from N threads yield one complete store dir, partial-dir-with-version.json no longer trusted, materialize idempotence, dev-mode copy-not-move.
- `test_app_nginx_manager.py` — atomic config write (no partial file observable), concurrent register/unregister serialization, single atexit registration. Test-isolation hooks already exist (`get_nginx_config_dir` scopes to the test folder, app_nginx_manager.py:336-345).
- Build-lock test — N threads through `_build_frontend` with a stubbed shell proxy: 1 build runs, N−1 reuse (same resource) / are serialized.
- `AppLogContext` propagation test — record emitted from a ShellProxy reader thread carries the context_id.

---

# PART B — Instance-independent builds + shared build cache (PR 2, after Part A)

The backend URL is baked because `rxconfig.py` reads `GWS_REFLEX_API_URL` at build time; it lands in exactly one predictable file (`assets/reflex-env-<hash>.js`). A second baked per-instance value exists: the **app_id**, compiled into initial state via `@rx.var get_reflex_user_auth_info_with_system_fallback` (`reflex_main_state.py:93+` reading `GWS_APP_ID`), in an *unpredictably named* chunk — the URL fix alone is not sufficient for sharing builds.

## B1. Same-origin routing (removes the baked URL)

**Mechanism — `GWS_REFLEX_API_URL` is not removed; its build-time value changes.** User `rxconfig.py` files keep reading it unchanged. For the `reflex export` command only, gws_core sets `GWS_REFLEX_API_URL=http://localhost:<external_port>`, so the baked URLs contain no instance id (`ws://localhost:<port>/gws-back/_event`). In the browser, Reflex's own `getBackendURL()` (`state.js:94-118`) replaces a literal `localhost` hostname with `window.location.hostname` — the browser derives the real host from the page's own address (works for id hosts *and* custom-subdomain aliases; https drops the port and upgrades ws→wss). The instance-specific part moves into nginx (already generated per instance): the front block routes `/gws-back/` to that instance's backend port. The backend *runtime* env keeps `GWS_REFLEX_API_URL` = the `-back` URL as today, so old builds, dev mode, the download service, and user code reading it stay working.

- **Build env only** (in `_build_frontend`, prod): `GWS_REFLEX_API_URL=http://localhost:<external_port>` + `REFLEX_BACKEND_PATH=/gws-back` + `GWS_REFLEX_BUILD_MODE=1`. Reflex's env override beats rxconfig kwargs (`reflex_base/config.py:356-358`) — **no user brick regenerates anything**. Under local http the baked external port matches because all nginx services listen on that one shared port. CORS becomes unnecessary for new builds.
- **Runtime env unchanged** — backend keeps serving `/_event`, `/ping`, `/_upload` at root; add `GWS_REFLEX_BACKEND_PREFIX=/gws-back` for the download service.
- **nginx:** `AppNginxReflexFrontServerServiceInfo` gains `location ^~ /gws-back/ { proxy_pass http://127.0.0.1:<back_port>/; ... }` (trailing slash strips the prefix; `^~` beats the asset regex at app_nginx_service.py:230; websocket upgrade headers as in the redirect service). Keep the `-back` server blocks + CORS untouched so old per-resource builds keep working — remove in a later release.
- **De-bake app_id:** under `GWS_REFLEX_BUILD_MODE=1`, `_build_user_auth_info` returns `None` and `get_app_id()` returns a sentinel (`reflex_main_state.py:76-93`, `reflex_main_state_base.py:210-218`). `None` auth info is already a legal pre-hydration state (public apps); real values arrive on websocket hydration from the per-instance backend.
- **Download service** (`gws_reflex_download_service.py:169-173`): if `GWS_REFLEX_BACKEND_PREFIX` set, emit relative `/gws-back/gws_reflex_download/<token>`; keep the absolute fallback for dev.

## B2. Shared build cache (1 build for N instances)
- New `src/gws_core/apps/reflex/reflex_front_build_cache.py`. Scope: **AppConfig-based apps only** (code fixed by brick version); static-folder apps keep per-resource builds (their code differs per resource).
- Key: `<brick-data>/<brick_name>/reflex-front-builds/<app typing name>/<brick_version>--<env_hash>` where `env_hash` covers external port + backend path + format version.
- Fill: export into a tmp dir under the cache root, validate, `os.replace()` (atomic, under the A2 app-folder lock); GC sibling entries on store. On hit: copy into the per-resource folder — `get_front_build_path_if_exists()` / `update_front_build_info()` semantics untouched, nginx keeps serving from the per-resource folder.
- Guardrail: after export, grep the bundle for the builder's resource id; if found (user app baked instance env at module scope), log a warning and skip caching that app.

## B3. Runtime verification for Part B (cannot be proven statically)
- Export with `REFLEX_BACKEND_PATH` → inspect `assets/reflex-env-*.js` for `ws://localhost:<port>/gws-back/_event`.
- Local http lab: websocket connect, upload, download, gws_code auth flow through `/gws-back`.
- Prod https lab incl. custom subdomain; old build coexisting with new nginx config; one reflex-enterprise app (its endpoint prefixing under `backend_path` is unverified).
- Confirm the baked initial state contains no app_id and components render pre-hydration.

---

## Delivery

- **PR 1 (Part A):** four commits — A1 plugin store, A2 build lock, A3 nginx, A4+A5 logging & tests. Closes the crash/race content of #103.
- **PR 2 (Part B):** B1 then B2 (B2 must not ship without B1). Reference #103; open a dedicated issue for it (also split the nginx race into its own issue per the comment, closed by PR 1).
- Out of scope (noted in #103, need their own investigations): `app_config.json` teardown-ordering error, `gws_ai_toolkit-db` container unreachable, nginx reload debounce.

## Verification (Part A)

1. `cd bricks/gws_core && gws server test test_app_plugin_downloader`, `test_app_nginx_manager`, the build-lock test, `test_reflex_app`, `test_streamlit_app`, `test_compress` (targeted runs).
2. `ruff check --fix` on modified files.
3. Manual smoke: start the reflex showcase app twice concurrently (two resources) — expect exactly one `reflex export` at a time, zero `unzip` errors, zero `pread()` nginx errors; kill all apps and restart 2 — nginx reloads cleanly.
4. Check the log: MAIN records during a build carry the app's `context_id`; `AppsManager.get_logs_of_app` shows build/nginx lines; build start/end pairs present with duration.

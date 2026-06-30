# Custom subdomain for apps — implementation plan (alias / front-only / live)

## Context

Today, every Streamlit/Reflex app is reachable at a host derived from its database id:
`{app_sub_domain}-{resource_model_id}.{virtual_host}` (prod) — e.g. `app-dev-3f2a...8b.lab.example.com`.
The id is opaque and unstable across re-publishes (a new resource = a new id = a new URL).

This feature lets a user **optionally** assign a readable, stable custom subdomain (e.g.
`app-hello-world`) as an **additional, aliased** entry point to the app, while keeping the
id-based host as the canonical URL.

### Decisions (agreed)
- **Alias, both hosts live.** The custom host does **not** replace the id host. The app's
  canonical URL (the one returned by `get_host_url` / `get_app_full_url`, and the backend URL
  baked into Reflex builds) stays id-based and stable. The custom host is registered as an
  **extra `server_name`** on the same nginx front block, resolving to the same backend.
  This is the nginx-level meaning of "the custom domain returns the same as the id domain".
- **Front only.** The alias is attached to the *front* service only:
  - Streamlit: its single redirect service (that *is* the front).
  - Reflex: the front static-file service. The `-back` redirect service keeps **only** the
    id-based host — the backend stays id-based.
- **Live.** Setting/clearing the custom subdomain on a *running* app re-registers its front
  nginx service(s) and reloads nginx immediately — no restart required. On a stopped app it
  takes effect on next start (the host is rebuilt from the persisted value).
- **Alias mechanism:** a single nginx `server` block lists multiple names
  (`server_name id-host custom-host;`). `AppNginxServiceInfo.server_name` becomes
  `str | list[str]`.
- **Reflex CORS:** because the custom-origin front calls the id-based backend cross-origin,
  the backend's `Access-Control-Allow-Origin` must also accept the custom front origin.
- **Host format:** the custom value still gets the `Settings.get_app_sub_domain()` prefix and the
  same local/prod formatting as the id host. Only the middle segment differs
  (`custom_subdomain` instead of `resource_model_id`). Stays inside the reserved `app-dev-*`
  routing band, so **no nginx/infra change is required**.
- **Dev mode:** custom subdomain is ignored in dev mode (`DEV_MODE_APP_ID` is always used).

## Current state (already implemented — keep)
- `AppInstance.custom_subdomain` + `set_custom_subdomain` — `apps/app_instance.py:29,116`.
- `AppInstanceDTO.custom_subdomain` + populated in `to_dto` — `apps/app_dto.py:47`,
  `apps/app_instance.py:180`.
- `AppResource` persisted field `_custom_subdomain` (DATABASE storage), getter/setter,
  `_validate_custom_subdomain`, `_check_custom_subdomain_unique`, and the
  `app.set_custom_subdomain(...)` call in `default_view` — `apps/app_resource.py`.
- REST routes `PUT /apps/{id_}/custom-subdomain/{subdomain}` and
  `DELETE /apps/{id_}/custom-subdomain` — `apps/app_controller.py:60-89`.
- `AppsManager.set_custom_subdomain` — persists the value — `apps/apps_manager.py:282-304`.

**What changes from the old plan:** the host is no longer *replaced* by the custom value.
Routing becomes an alias on the front nginx block, applied live.

## Changes

### 1. `apps/app_process.py` — stop overriding the host; expose the alias host
- **Revert `get_host_name`** (`app_process.py:276-298`) so it never uses `custom_subdomain`.
  Precedence becomes dev mode > id again:
  ```python
  if self._app.is_dev_mode():
      host_name = self.DEV_MODE_APP_ID
  else:
      host_name = self._app.resource_model_id
  ```
  (Restores the stable id-based canonical host used by `get_host_url`, `get_app_full_url`,
  the baked Reflex backend URL, and the front health check at `reflex_process.py:283`.)
- **Add `get_custom_host_name(self, suffix: str = "") -> str | None`**: returns `None` when
  `self._app.custom_subdomain` is falsy or in dev mode; otherwise builds the host with the
  **same** local/prod formatting as `get_host_name`, substituting `custom_subdomain` for the
  id segment. Factor the shared formatting (`is_local_or_desktop_env` branch + prefix/virtual
  host) into a small private helper used by both methods to avoid drift.
- **Add `get_front_server_names(self, suffix: str = "") -> list[str]`** (or compute inline in
  the process subclasses): `[get_host_name(suffix)]` plus `get_custom_host_name(suffix)` when
  not `None`. Used as the front service `server_name`.

### 2. `apps/app_nginx_service.py` — allow multiple server names
- `AppNginxServiceInfo.server_name: str | list[str]` (constructor accepts either).
- In both `get_nginx_service_config` templates, render the names joined by spaces:
  add a helper `self._render_server_names()` returning
  `self.server_name if isinstance(self.server_name, str) else " ".join(self.server_name)`
  and use it in the `server_name {...};` line (`app_nginx_service.py:71` and `:114`).
- `AppNginxRedirectServiceInfo`: `allowed_origin` currently a single origin string. nginx's
  `add_header 'Access-Control-Allow-Origin'` only emits one value and
  `Access-Control-Allow-Credentials: true` forbids `*`. To allow **both** the id-based and the
  custom front origin, change CORS to echo the request origin when it is in an allow-list:
  - accept `allowed_origins: list[str] | None` (keep `allowed_origin` as a back-compat
    single-value alias, or migrate the one caller),
  - emit an nginx `if` that sets a variable to `$http_origin` only when it matches one of the
    allowed origins, then `add_header 'Access-Control-Allow-Origin' $cors_origin always;`.
    (A per-server `map` is cleaner but `map` must live in the `http` block; an `if
    ($http_origin ~ '^(origin1|origin2)$')` inside the `location` is acceptable and keeps the
    change local to the service block.)

### 3. `apps/streamlit/streamlit_process.py` — alias on the single service
- `_get_nginx_services` (`streamlit_process.py:160-168`): set
  `server_name=self.get_front_server_names()` instead of `self.get_host_name()`.
  (Streamlit has no separate backend, so no CORS change.)

### 4. `apps/reflex/reflex_process.py` — alias on front, CORS on back
- `_get_prod_nginx_services` (`reflex_process.py:243-249`): front
  `AppNginxReflexFrontServerServiceInfo` gets `server_name=self.get_front_server_names()`.
- `_get_cloud_back_nginx_services` (`reflex_process.py:256-265`): **leave `server_name` as
  `self.get_host_name("-back")`** (backend stays id-only). Change its CORS to allow both front
  origins: pass `allowed_origins=[self.get_host_url(), <custom front url>]`, where the custom
  front url is built from `get_custom_host_name()` via the same `https://`/`http://…:port`
  wrapping as `get_host_url` (add `get_custom_host_url()` mirroring `get_host_url`, or compute
  from `get_custom_host_name`). When there is no custom subdomain, the list is just the id
  front origin (current behavior).
- Dev services (`_get_dev_nginx_services`, `:98-107`) unchanged — dev ignores custom subdomain.

### 5. `apps/apps_manager.py` — apply live
Update `set_custom_subdomain` (`apps_manager.py:282-304`) so after persisting it pushes the
change onto a running process, mirroring how `set_stop_policy` updates the live process
(`apps_manager.py:276-279`):
```python
resource.set_custom_subdomain(subdomain)
resource_model.update_resource_fields(resource)

app_process = cls.find_app_by_resource_model_id(app_id)
if app_process is not None:
    app_process.update_custom_subdomain(subdomain)
```
- Add `AppProcess.update_custom_subdomain(self, subdomain: str | None) -> None`:
  - `self._app.set_custom_subdomain(subdomain)` (updates the in-memory AppInstance);
  - if the process is running and has services, **rebuild the front service(s)** with the new
    `server_name` list and re-register them. Re-registration is idempotent: `register_services`
    overwrites `self._services[service_id]` by id and reloads nginx
    (`app_nginx_manager.py:90-98`), so calling it again with the same front `service_id`
    replaces the block in place — no `unregister` needed. For Reflex, also rebuild the `-back`
    service so its CORS allow-list picks up / drops the custom front origin.
  - Simplest robust implementation: re-run the subclass `_get_*_nginx_services()` builder and
    `register_services(...)` the result (front + back). Keep `self._services` in sync with what
    was registered. If not running, do nothing (next start rebuilds from the persisted value).
- Update the docstring: change "takes effect on the next start" to "applied immediately if the
  app is running; otherwise on next start."

### 6. REST layer — no change
Routes already call `AppsManager.set_custom_subdomain`; the live behavior is gained for free.
Update the route docstrings (`app_controller.py:71,86`) to drop "takes effect on the next
start" wording.

## Verification

### Unit tests — rewrite the existing host assertions (contract changed)
The current tests assert the **old replace semantics** and must be updated:
- `tests/test_gws_core/test_streamlit_app.py:41-62` (`test_custom_subdomain_host_name`,
  `test_dev_mode_ignores_custom_subdomain`) — `get_host_name()` no longer returns the custom
  host. Replace with:
  - `get_host_name()` stays id-based even when a custom subdomain is set.
  - `get_custom_host_name()` returns the custom-based host; `None` when unset.
  - the front service's `server_name` is a list containing **both** the id host and the custom
    host; `get_host_name("-back")`/backend service still id-only.
- `tests/test_gws_core/test_reflex_app.py:27-43` (`test_custom_subdomain_host_name`) — same:
  front service has both names, `-back` service has only the id host.
- Keep the validation/uniqueness/clear/dev-mode tests
  (`test_streamlit_app.py:65-108`) — those exercise the resource layer and are unchanged.

### New tests
- **Alias present:** build a resource with `set_custom_subdomain("app-hello-world")`, run
  `default_view`, fetch the process via `AppsManager.find_app_by_resource_model_id`, inspect the
  generated front service: assert its `server_name` list contains both
  `_expected_host("resource-model-id")` and `_expected_host("app-hello-world")`.
- **Backend id-only (Reflex):** assert the `-back` service `server_name` == id-based `-back`
  host, and its CORS allow-list contains the custom front origin.
- **Live update:** with a running app, call `AppsManager.set_custom_subdomain(id, "x")`, assert
  the front service in `AppNginxManager.get_instance().get_service(<front_id>)` now carries the
  new alias; then clear it and assert the alias is gone — all without restarting.
- **Default unchanged:** no custom subdomain → front `server_name` is just the id host (string
  or single-element list, per implementation).

### Run
`cd bricks/gws_core && gws server test test_streamlit_app` and `gws server test test_reflex_app`.

### Manual (optional)
`gws streamlit run <config>` after setting a custom subdomain; confirm both the id-based URL and
the custom URL serve the app. For Reflex prod, confirm the custom-origin front successfully
calls the id-based backend (no CORS error in the browser console).

## Notes / risks
- `running_processes` stays keyed by `resource_model_id` — only host/URL/nginx changes.
- The one real correctness risk is the Reflex CORS echo: verify the `if ($http_origin ~ ...)`
  block emits exactly one `Access-Control-Allow-Origin` and coexists with the existing
  `Access-Control-Allow-Credentials: true` (no `*`).
- `server_names_hash_bucket_size 128` is already set (`app_nginx_manager.py:57`), so longer
  combined names are fine.

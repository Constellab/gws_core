# Custom subdomain for apps — implementation plan

## Context

Today, every Streamlit/Reflex app is reachable at a host derived from its database id:
`{app_sub_domain}-{resource_model_id}.{virtual_host}` (prod) — e.g. `app-dev-3f2a...8b.lab.example.com`.
The id is opaque and unstable across re-publishes (a new resource = a new id = a new URL).

This feature lets a user **optionally** assign a readable, stable custom subdomain (e.g.
`app-hello-world`) so the app is reachable at `{app_sub_domain}-app-hello-world.{virtual_host}`, while
keeping the current id-based behavior as the default when no custom subdomain is set. Because two apps
sharing a subdomain would collide in nginx routing, setting one is guarded by a **lab-wide uniqueness
check**.

### Decisions
- **Host format:** the custom value still gets the `Settings.get_app_sub_domain()` prefix — i.e.
  `{sub_domain}-{custom_subdomain}.{virtual_host}`. Only the middle segment changes
  (`custom_subdomain` instead of `resource_model_id`). This stays inside the existing reserved
  `app-dev-*` routing band, so **no nginx/infra change is required**.
- **Uniqueness scope:** DB-wide — check across all persisted Streamlit/Reflex AppResources in the
  lab, not just running ones.
- **API surface:** code setter/getter on `AppResource` **plus** a REST endpoint (mirroring the
  existing stop-policy endpoint).
- **Dev mode:** custom subdomain is ignored in dev mode (keeps `DEV_MODE_APP_ID`). It applies in
  local/desktop and prod.

## Key existing code being reused
- Host construction: `AppProcess.get_host_name()` — `src/gws_core/apps/app_process.py:276-290`.
- RField with SQL-queryable persistence: `StrRField(storage=RFieldStorage.DATABASE)` lands in the
  queryable `ResourceModel.data` JSON column (`src/gws_core/resource/r_field/r_field.py:86-119`).
  Existing AppResource fields (`_requires_authentification`, `_stop_policy`) use the default KV_STORE
  and are *not* queryable — the new field must use DATABASE.
- AppResource setter convention: `set_stop_policy` / `get_stop_policy` — `app_resource.py:153-165`.
- Threading a value onto the AppInstance in `default_view`: `app_resource.py:355-362`
  (`app.set_params`, `app.set_stop_policy`).
- Query AppResources by type: `ResourceModel.select().where(ResourceModel.resource_typing_name == ...)`
  — precedent at `src/gws_core/apps/streamlit/streamlit_resource.py:142`.
- REST + service update pattern: `app_controller.py:44-57` (`set_stop_policy` route) →
  `AppsManager.set_stop_policy` (`apps_manager.py:259-279`, loads ResourceModel → resource → setter →
  `resource_model.update_resource_fields(resource)`).

## Changes

### 1. `apps/app_resource.py` — persisted field, validation, uniqueness, setters
- Import `RFieldStorage` (from `gws_core.resource.r_field.r_field`).
- Add field after line 56:
  ```python
  _custom_subdomain: str = StrRField(storage=RFieldStorage.DATABASE)
  ```
- Add methods (mirroring `get/set_stop_policy`):
  - `get_custom_subdomain() -> str | None` — return `self._custom_subdomain or None`.
  - `set_custom_subdomain(subdomain: str | None)` — if falsy, clear it; else validate, run the
    uniqueness check, then store the normalized value.
  - `_validate_custom_subdomain(subdomain: str) -> str` (staticmethod) — lowercase, then enforce a
    DNS label: regex `^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$`. Raise `BadRequestException` on invalid.
    Reject the reserved value `dev-app` (= `AppProcess.DEV_MODE_APP_ID`).
  - `_check_custom_subdomain_unique(subdomain: str)` — DB-wide check:
    query `ResourceModel.select().where(ResourceModel.resource_typing_name.in_([<all AppResource
    subclass typing names>]))`, load each resource, and raise `BadRequestException` if any *other*
    resource (id != `self.get_model_id()`) returns the same `get_custom_subdomain()`. Use a
    Python-side comparison (not a fragile `data LIKE`) — app counts are modest. Get the subclass
    typing names via the resource typing registry for `AppResource` descendants (Streamlit + Reflex);
    a small helper listing the two concrete typing names is acceptable.
- In `default_view` (after `app.set_stop_policy(...)`, ~line 362):
  ```python
  app.set_custom_subdomain(self.get_custom_subdomain())
  ```

### 2. `apps/app_instance.py` — carry the value to the process
- Add field `custom_subdomain: str | None = None`.
- Add `set_custom_subdomain(self, subdomain: str | None) -> None` (mirrors `set_stop_policy`).

### 3. `apps/app_process.py` — use it in `get_host_name`
Rewrite `get_host_name` (276-290). Precedence: dev mode > custom > id. The custom value **keeps the
`sub_domain` prefix**:
```python
def get_host_name(self, suffix: str = "") -> str:
    if self._app.is_dev_mode():
        host_name = self.DEV_MODE_APP_ID
    else:
        host_name = self._app.custom_subdomain or self._app.resource_model_id

    if Settings.is_local_or_desktop_env():
        return f"{host_name}{suffix}.localhost"

    sub_domain = Settings.get_app_sub_domain()
    virtual_host = Settings.get_virtual_host()
    return f"{sub_domain}-{host_name}{suffix}.{virtual_host}"
```
Resulting hosts:
- Default prod: `app-dev-{resource_model_id}{suffix}.{virtual_host}` (unchanged).
- Custom prod: `app-dev-app-hello-world{suffix}.{virtual_host}` (`-back` suffix still appended for
  the Reflex backend host).
- Local: `app-hello-world{suffix}.localhost`.

Note: the `running_processes` dict in `AppsManager` stays keyed by `resource_model_id` — only the
*host/URL* changes, so no change to process registration/lookup is needed.

### 4. REST endpoint — `apps/app_controller.py` + `apps/apps_manager.py`
- `apps_manager.py`: add classmethod `set_custom_subdomain(app_id, subdomain)` mirroring
  `set_stop_policy` (`apps_manager.py:259-279`): load `ResourceModel.get_by_id_and_check`, assert it's
  an `AppResource`, call `resource.set_custom_subdomain(subdomain)` (this runs validation +
  uniqueness), `resource_model.update_resource_fields(resource)`. If the app is currently running,
  the new host only takes effect on next start (document in the docstring; optionally stop the running
  process so it restarts with the new host).
- `app_controller.py`: add a route mirroring the stop-policy one:
  ```python
  @core_app.put("/apps/{id_}/custom-subdomain/{subdomain}", tags=["App"],
                summary="Set the custom subdomain for an app")
  def set_custom_subdomain(id_: str, subdomain: str,
                           _=Depends(AuthorizationService.check_user_access_token)) -> None:
      return AppsManager.set_custom_subdomain(id_, subdomain)
  ```
  Consider also an empty/clear form (pass empty → clears the custom subdomain).

## Verification
1. **Unit tests** (extend `tests/test_gws_core/test_streamlit_app.py`, `test_reflex_app.py`):
   - Build a `StreamlitResource`, `set_custom_subdomain("app-hello-world")`, save via `ResourceModel`,
     run `default_view`, fetch the process via
     `AppsManager.find_app_by_resource_model_id(model_id)`, assert
     `process.get_host_name() == "app-hello-world.localhost"` (test env is local) and
     `process.get_host_name("-back") == "app-hello-world-back.localhost"`.
   - Validation: uppercase / leading dash / invalid chars / `dev-app` all raise.
   - Uniqueness: two saved AppResources, setting the same subdomain on the second raises.
   - Default unchanged: with no custom subdomain, `get_host_name()` still uses `resource_model_id`.
2. Run: `cd bricks/gws_core && gws server test test_streamlit_app` and `gws server test test_reflex_app`.
3. Manual (optional): `gws streamlit run <config>` after setting a custom subdomain, confirm the dev
   URL uses the custom segment.

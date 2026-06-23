# Config form (ConfigSpecs) for entity action buttons — implementation plan

## Context

Entity actions (`src/gws_core/entity_action/`) let a brick contribute menu buttons/links to an
entity (resource, note, scenario, …). Today a button is a fire-and-forget callback: clicking it
POSTs to `POST /entity-action/{type}/{id}/{action_name}` with **no body**, and the owning plugin's
`execute_action(entity, action_name)` runs.

We want a button to optionally declare a **`ConfigSpecs`** — the same object used by
`credentials/credentials_type.py`. When provided:

- The action DTO sent to the front carries the **serialized specs**, so on click the front renders
  a **form** from them (the front already renders `dict[str, ParamSpecDTO]` for credentials).
- On submit, the front POSTs the **dict of values** in the request body.
- The plugin's `execute_action` receives that raw dict and does whatever it wants with it.

### Decisions (agreed with user)
- `execute_action` **always** gains a third arg `config_params: ConfigParamsDict` (a plain
  `dict[str, ParamValue]`). For buttons with no specs it is `{}`.
- The **service does NOT validate** the values and does **NOT** re-run `get_actions` to look up
  specs. It passes the raw request body straight through. The plugin decides whether/how to
  validate (e.g. by calling `self.SPECS.get_and_check_values(config_params)` itself).
- `config_specs` therefore travels **one way only**: backend → DTO → front (for form rendering).
- No persistence: submitted values are transient per click, not stored.

## Backend changes

### 1. `entity_action.py` — builder carries the specs
`src/gws_core/entity_action/entity_action.py`
- Add field `config_specs: ConfigSpecs | None` to `EntityAction` (class attr + `__init__`).
- Add `config_specs: ConfigSpecs | None = None` to `EntityAction.button(...)` (link does NOT get it).
- In `to_dto()`, for BUTTON kind, set the DTO's `config_specs` to `self.config_specs.to_dto()` when
  present, else `None`.
- Import `ConfigSpecs` from `gws_core.config.config_specs`.

### 2. `entity_action_dto.py` — DTO exposes specs to the front
`src/gws_core/entity_action/entity_action_dto.py`
- Add to `EntityActionButtonDTO`:
  `config_specs: dict[str, ParamSpecDTO] | None = None`
- Import `ParamSpecDTO` from `gws_core/config/param/param_types.py`.
- This is the exact shape `credentials` already sends (produced by `ConfigSpecs.to_dto()`), so the
  front reuses its existing form renderer.

### 3. `entity_action_plugin.py` — execute signature gains config_params
`src/gws_core/entity_action/entity_action_plugin.py`
- New abstract signature:
  `def execute_action(self, entity: Model, action_name: str, config_params: ConfigParamsDict) -> EntityActionResultDTO`
- Import `ConfigParamsDict` from `gws_core.config.config_params` (`= dict[str, ParamValue]`,
  `config_params.py:5`).
- Docstring: `config_params` is the raw, **unvalidated** dict of form values (empty `{}` for buttons
  without specs); the plugin owns any validation.

### 4. `entity_action_controller.py` — accept an optional body on execute
`src/gws_core/entity_action/entity_action_controller.py`
- Add a request body to `execute_entity_action`:
  `config_params: ConfigParamsDict | None = Body(default=None)`
  (import `Body` from fastapi, `ConfigParamsDict` from config_params).
- Pass through:
  `EntityActionService.execute_entity_action(entity_type, entity_id, action_name, config_params)`.
- Body stays optional so existing no-form buttons work with an absent/empty body.

### 5. `entity_action_service.py` — pass raw dict through (no validation)
`src/gws_core/entity_action/entity_action_service.py`
- `execute_entity_action` gains `config_params: ConfigParamsDict | None = None`.
- Normalize `None → {}`, then `plugin.execute_action(entity, local_name, config_params)`.
- Do **not** look up specs, do **not** validate. Import `ConfigParamsDict`.

### 6. Update the one existing plugin
`src/gws_core/apps/app_stop_policy_action_plugin.py`
- Update its `execute_action` to the new 3-arg signature (ignores `config_params`).

## Reused existing pieces (do not reinvent)
- `ConfigSpecs` + `to_dto()` / `get_and_check_values()` — `src/gws_core/config/config_specs.py`.
- `ParamSpecDTO` — `src/gws_core/config/param/param_types.py`.
- `ConfigParamsDict = dict[str, ParamValue]` — `src/gws_core/config/config_params.py:5`.
- Reference flow: `credentials_service.get_credentials_data_specs` → front renders form.

---

## FRONTEND CONTRACT — what changes for the front

This section is the hand-off for the front-end team. Two API endpoints are affected; both are
**backward compatible** (new fields are optional / nullable).

### A. `GET /entity-action/{entity_type}/{entity_id}` — menu now MAY carry a form spec

`EntityActionButtonDTO` gains one new **optional, nullable** field: `config_specs`.

Before:
```jsonc
{
  "type": "button",
  "text": "Run analysis",
  "action_name": "gws_core.my_plugin.run",
  "icon": "play_arrow",
  "divider": false,
  "disabled": false,
  "color": null,
  "children": null
}
```

After (button WITH a form):
```jsonc
{
  "type": "button",
  "text": "Run analysis",
  "action_name": "gws_core.my_plugin.run",
  "icon": "play_arrow",
  "divider": false,
  "disabled": false,
  "color": null,
  "children": null,
  "config_specs": {                     // NEW — null/absent when the button has no form
    "threshold": {
      "type": "int",
      "optional": false,
      "visibility": "public",
      "default_value": 10,
      "additional_info": {},
      "human_name": "Threshold",
      "short_description": "Cut-off value"
    },
    "label": { "type": "str", "optional": true, "visibility": "public", ... }
  }
}
```

- `config_specs` is **`null` (or absent)** for buttons with no form → behave exactly as today
  (click → POST immediately, no dialog).
- When `config_specs` is a non-empty object, it is a **`dict<paramName, ParamSpecDTO>`** — the
  **same `ParamSpecDTO` shape already used by the credentials form** (`/credentials/data/specs`).
  **Reuse the existing config-form / dynamic-form renderer.** No new field types.

### Front behaviour on click
- **No `config_specs`** → POST the execute endpoint immediately, no body (current behaviour).
- **Has `config_specs`** → open the config form dialog, collect values, then POST the execute
  endpoint with the values as the JSON body (see B). Cancel = no request.

### B. `POST /entity-action/{entity_type}/{entity_id}/{action_name}` — now accepts a body

The execute endpoint now accepts an **optional JSON body**: the dict of form values keyed by param
name (the output of the config form), e.g.:
```jsonc
// request body
{ "threshold": 25, "label": "high" }
```
- For buttons **without** a form: send **no body** (or `null`) — unchanged from today.
- For buttons **with** a form: send the collected values dict as the JSON body.
- Response is unchanged: `EntityActionResultDTO` (`navigate_to`, `navigate_query_params`,
  `open_in_new_tab`, `message`).
- NOTE: the backend does **not** validate these values against the spec (the plugin may). The
  front should still validate against `config_specs` before sending, using the same rules it
  already applies to credential/config forms (required fields, types).

### Front DTO/type updates needed
- Add optional `configSpecs?: { [key: string]: ParamSpecDTO } | null` to the front
  `FlMenuDynamicButton` (or its DTO mapping) — mirrors backend `EntityActionButtonDTO.config_specs`.
- Wire the execute call to optionally send the values dict as the POST body.

---

## Verification (backend)

1. **Lint**: `ruff check --fix` on each modified file.
2. **Existing tests**: from `bricks/gws_core`, find the entity_action test in `tests/` and run it
   (e.g. `gws server test test_entity_action`). Confirms get_actions/execute still pass under the
   new signature.
3. **New/extended test** in the entity_action test:
   - Test plugin whose `get_actions` returns
     `EntityAction.button(..., config_specs=ConfigSpecs({"threshold": IntParam()}))`.
   - Assert `get_entity_actions(...)` returns a button DTO with non-empty
     `config_specs` (`dict[str, ParamSpecDTO]`, key `"threshold"`); a button without specs →
     `config_specs is None`.
   - `execute_entity_action(type, id, "<plugin_id>.act", {"threshold": 5})` → plugin received
     `{"threshold": 5}` (echo back in `message`).
   - execute with no body → plugin received `{}`.
4. **Manual**: `gws server run`; `GET /entity-action/{type}/{id}` shows `config_specs` on the
   button; `POST .../{action_name}` with a JSON values body round-trips into the plugin.

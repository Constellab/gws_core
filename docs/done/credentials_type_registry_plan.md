# Plan: Replace `CredentialsType` enum with a decorator-based registry

## Goal
Delete the `CredentialsType` enum and the hardcoded `Credentials.get_data_types()` dict.
Replace them with a `@credentials_type("...")` decorator (mirroring `@entity_action_plugin`)
so any brick can register its own credentials data class. The built-in 5 types are converted
to the new system. `CredentialsParam` accepts a credentials data **class** instead of an enum value.

## Identity & storage decisions (confirmed with user)
- Each data class is registered with a brick-namespaced string id:
  `@credentials_type("s3")` declared in `gws_core` -> stored id `"gws_core.s3"`.
- The DB `type` column stays a string but becomes a `TypedCharField` (no longer
  `TypedEnumField(choices=...)`). It stores the namespaced id.
- A migration rewrites existing rows:
  `BASIC -> gws_core.basic`, `S3 -> gws_core.s3`, `S3_LAB_SERVER -> gws_core.s3_lab_server`,
  `LAB -> gws_core.lab`, `OTHER -> gws_core.other`.

---

## New files

### 1. `credentials/credentials_registry.py` - global registry (mirrors `EntityActionRegistry`)
- `_data_types: dict[str, type[CredentialsDataBase]]` keyed by `type_id`.
- `register(cls)`, `get_data_type(type_id) -> type[CredentialsDataBase] | None`,
  `get_all() -> dict`, `get_all_ids() -> list[str]`. Raises on duplicate id.

### 2. `credentials/credentials_decorator.py` - `@credentials_type(unique_name)` (mirrors `entity_action_decorator.py`)
- Validates subclass of `CredentialsDataBase`, validates `unique_name` is alphanumeric
  (`StringHelper.is_alphanumeric`).
- Sets `__credentials_type_name__ = unique_name` and
  `__credentials_type_id__ = f"{brick_name}.{unique_name}"` via `BrickHelper.get_brick_name`.
- Calls `CredentialsRegistry.register(cls)`.

---

## Changes to existing files

### 3. `credentials/credentials_type.py`
- **Delete** the `CredentialsType` enum entirely.
- Add a `get_type_id()` classmethod to `CredentialsDataBase` returning `cls.__credentials_type_id__`.
- Decorate the 5 data classes: `@credentials_type("basic")`, `@credentials_type("s3")`,
  `@credentials_type("s3_lab_server")`, `@credentials_type("lab")`, `@credentials_type("other")`.
- Change DTOs `CredentialsDTO`, `SaveCredentialsDTO`, `CredentialsDataTypeSpecDTO`:
  field `type: CredentialsType` -> `type: str` (the namespaced id).
- Note: a frontend-facing display name is preserved via `human_name`/specs; the raw id is what's stored & sent.

### 4. `credentials/credentials.py`
- `type = TypedEnumField(choices=CredentialsType)` -> `type = TypedCharField(max_length=255)`.
- `get_credentials_data_type()` -> `CredentialsRegistry.get_data_type(self.type)`.
- Delete `get_data_types()`.
- `find_by_name_and_check` / `search_by_type` / `search_by_types` / `search_by_name_and_type`:
  param type `CredentialsType` -> `str` (type id). Comparisons become string comparisons
  (Peewee handles this transparently).

### 5. `credentials/credentials_param.py` - the key API change
- Constructor: `credentials_type: CredentialsType | None` ->
  `credentials_type: type[CredentialsDataBase] | None` (pass the class directly,
  e.g. `CredentialsParam(CredentialsDataS3)`).
- Internally resolve to the string id via `credentials_type.get_type_id()` for storage in
  `additional_info` and for `find_by_name_and_check`.
- `human_name` default derived from the id / data class.

### 6. `credentials/credentials_service.py`
- Replace `CredentialsType.X` references with the corresponding data class ids:
  - `get_s3_credentials_data_by_access_key`:
    `search_by_types([CredentialsDataS3.get_type_id(), CredentialsDataS3LabServer.get_type_id()])`.
  - `get_lab_credentials_by_api_key`: `CredentialsDataLab.get_type_id()`.
  - basic helpers (`get_or_create_basic_credential`, `update_basic_credential`, type checks):
    `CredentialsDataBasic.get_type_id()`.
- `get_credentials_data_specs()`: iterate `CredentialsRegistry.get_all()` instead of
  `Credentials.get_data_types()`.

### 7. Call sites passing the param (use the class now)
- `impl/s3/resource_downloader_s3.py:34`, `impl/s3/resource_uploader_s3.py:43`:
  `CredentialsParam(CredentialsDataS3)`.
- `lab/lab_model/lab_model_service.py:137`: `type=CredentialsDataLab.get_type_id()` when building
  `SaveCredentialsDTO`/`Credentials`.
- Any other `type=CredentialsType.X` construction sites.

### 8. `__init__.py`
- Remove `CredentialsType` export. Export `credentials_type` decorator, `CredentialsRegistry`,
  and keep the `CredentialsData*` classes exported (other bricks need them for `CredentialsParam`).

---

## Migration

### 9. New migration in `migration_0.py` (`@brick_migration("0.22.2", ...)`)
- Rewrite the `type` column on every `gws_credentials` row from old enum value -> new namespaced id,
  using a literal map:
  `{"BASIC": "gws_core.basic", "S3": "gws_core.s3", "S3_LAB_SERVER": "gws_core.s3_lab_server",
  "LAB": "gws_core.lab", "OTHER": "gws_core.other"}`.
  Done with raw SQL `UPDATE`s (the enum no longer exists in code, so don't reference `CredentialsType`).
- **Also fix the existing `Migration0112`** (migration_0.py:1344): it references
  `Credentials.type == CredentialsType.OTHER`. Since that runs against historical data with the old
  `"OTHER"` value, change it to the string literal `"OTHER"` so it stays correct and stops importing
  the deleted enum.

---

## Tests & verification
- `tests/test_gws_core/test_credentials.py` (lines 59, 81): replace `CredentialsType.OTHER` with
  `CredentialsDataOther` / its id.
- `bricks/gws_invest/tests/.../test_yousign_service.py:96` and stripe test: update to the new
  class-based param / id.
- Grep for any remaining `CredentialsType` references across **all** bricks after edits.
- Run `cd bricks/gws_core && gws server test test_credentials`, then run the migration locally and
  confirm existing rows resolve via `get_data_object()`.
- `ruff check --fix` on all modified files.

---

## Open considerations (flag, not block)
- **Frontend contract**: the specs endpoint `GET /credentials/data/specs` and the saved param
  `additional_info.credentials_type` now carry namespaced ids (`gws_core.s3`) instead of `S3`.
  If the lab-front UI hardcodes `"S3"`/`"BASIC"` strings, it needs a matching update. The frontend
  lives outside this repo, so call out the exact values that changed.
- `is_alphanumeric` must permit underscores (the existing entity_action decorator relies on the same
  rule for names like `s3_lab_server`) - confirm before relying on it.

---

## Reference context (current state, for the implementer)
- DB column today: `credentials.py:29` `type = TypedEnumField(choices=CredentialsType)`
  (stores enum `.value` string, non-nullable).
- Hardcoded type->class map today: `credentials.py:96-103` `get_data_types()`.
- Enum defined: `credentials_type.py:13-22` (BASIC, S3, S3_LAB_SERVER, LAB, OTHER).
- Pattern to mirror: `entity_action/entity_action_registry.py`, `entity_action/entity_action_decorator.py`,
  `entity_action/entity_action_plugin.py`.
- Latest gws_core migration: `0.16.0`; brick version `0.22.1` -> new migration `0.22.2`.

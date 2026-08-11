# Modular Apps Split — gws_core → core + workflow + note + form

## Overview

Today `gws_core` is a single brick containing every domain of the data lab: scenarios/resources/views, notes, forms, tags, users, file storage, rich text, etc. The goal of this refactor is to split it into **several applications that communicate with each other but can each run on their own**:

| Brick | Content | Main tables |
|---|---|---|
| `gws_core` (reduced) | Technical core: `Model`/`BaseModel`, DbManager + migrations, user/auth, settings, event bus, typing system, **generic rich text engine** (extracted from `impl/`), **file layer** (`FileStore`/`FSNodeModel`, extracted from `impl/file/` — see point 8), **tags**, extension registries (see below), **app engine** (`apps/` runtime: Streamlit/Reflex, gateway, auth — see point 9), `folder/` (SpaceFolder), space, `config/` (`ConfigSpecs`), activity log | `gws_user`, `gws_entity_tag`, `gws_fs_node`, `gws_file_store`, `gws_space_folder`… |
| `gws_workflow` | scenario, protocol, process, task, resource, view, view_config, scenario_template, `AppResource`, **all of `impl/`** (`File`/`Folder` *resources*, Table, agents…) minus the file layer and rich text engine which move to the core | `gws_scenario`, `gws_protocol`, `gws_task`, `gws_task_inputs`, `gws_resource`, `gws_view_config`, `gws_scenario_template` |
| `gws_note` | note, note_template | `gws_note`, `gws_note_template` |
| `gws_form` | form, form_template, form_template_version | `gws_form`, `gws_form_template`, `gws_form_template_version`, `gws_form_save_event` |

**Golden rule: an app never imports another app — only the core.** (One possible exception is under discussion: `gws_note` → `gws_workflow`, see point 15.) All cross-app collaboration goes through core-owned mechanisms:

- **Registries (sync)**: the core exposes extension points (entity types, rich text blocks, graph edges, ports/interfaces); each app registers its contributions at brick load time. A consumer asks the registry, never the providing app. If the provider is absent, the registry answers "nobody" and the consumer degrades gracefully.
- **Events (async)**: the existing event bus (`model/event/`). Apps subscribe by event name, never by importing the emitter. This is already how `form/form_note_join_listener.py` hooks into notes without `note` knowing `form`.
- **Soft references**: cross-app entities are referenced by `(entity_type, entity_id)` strings, never by FK. This is the pattern already proven by `tag/entity_tag.py`.

**Target deployment: modular monolith.** One server; each brick owns its tables and migrations (`@brick_migration` is already per-brick) and **zero FK between tables of different bricks** — which keeps a later split into separate services possible without paying its cost now. Whether the tables all live in one physical DB or in one DB per module is an open decision (point 12).

**Autonomy = installable à la carte.** A lab can run with only `gws_note`, or only `gws_workflow`. Content referencing an absent app stays intact (opaque JSON) and renders as an "unavailable" placeholder; installing the app later restores it.

The canonical example — *a note embedding a resource view*: `gws_workflow` registers the `resourceView` rich text block in the core registry (payload schema + renderer + reference extractor). The note stores the block as opaque JSON. On `NoteContentUpdatedEvent`, a core reconciler extracts references via the registry and maintains generic `EntityLink` rows (note → view, note → scenario). Rendering asks the registry for the block's renderer; deletion of a view first checks incoming links and applies the declared deletion policy. `gws_form` plugs `form`/`formTemplate` blocks in exactly the same way.

### Migration order

1. **Break the coupling hubs without moving files** (highest-value step, monolith keeps running):
   turn the global enums into type registries, refactor `entity_navigator` into a generic next/previous navigation system, invert the `view_config_service` → `NoteViewModel` dependency.
2. **Generalize the cross-domain join tables into `EntityLink`** + deletion policies (DB migration, drop cross-domain FKs).
3. **Extract the bricks** `gws_workflow`, `gws_note`, `gws_form` — mostly file moves at that point. Add architecture tests (import-linter or equivalent) to prevent import regressions.
4. **Validate à-la-carte installation**: boot a lab with each app combination and verify graceful degradation.

Frontend: not decided yet — `lab-front` stays a single app for now; it will need a core `capabilities` endpoint listing installed apps to hide absent sections.

---

## Points to settle

### 1. Tags: registered entity types instead of enums

The tag system must become configurable: no more closed `TagEntityType` enum (`tag/tag_entity_type.py`), but a core registry where each app **registers its taggable entity types** at brick load time. The core tag machinery (`EntityTag`, tag values, propagation flags) is already generic — it stores `(entity_type, entity_id)` strings with no FK — only the type list is hard-coded.

The same principle applies to the other closed enums that hard-code the domain list (`ActivityObjectType` in `user/activity/`, `RichTextBlockTypeStandard` in `impl/rich_text/block/rich_text_block.py` — see point 5). Registered type keys must keep the exact string values already persisted in DB rows and rich text JSON.

### 2. `entity_navigator` → generic navigation with next/previous methods

`entity_navigator/entity_navigator.py` imports every model of every domain (Form, Note, ResourceModel, ViewConfig, Scenario, TaskModel…). It is the #1 coupling hub.

Target: a generic navigation system in the core. Each app registers its navigable entity types, and each registration provides **methods to get the next and previous objects** of an entity (e.g. workflow registers: resource → next = views + consuming scenarios, previous = generating scenario; note registers: note → previous = embedded views). The core only owns the generic traversal (walk next/previous recursively, dedup, tag propagation) over whatever is registered — an absent app simply contributes no navigation.

### 3. Cross-domain join tables → generic `EntityLink`

`gws_note_view` (note↔ViewConfig, FK RESTRICT), `gws_note_scenario` (note↔scenario, CASCADE), `gws_note_form` (note↔form, RESTRICT), `gws_note_template_form_template` are all the same thing: a queryable projection of references contained in rich text.

Target: one core table `EntityLink(from_type, from_id, to_type, to_id, kind)` with **no FK**, maintained by the existing event-driven reconciliation (`note/note_view_join_listener.py` pattern generalized: block registry exposes a reference extractor per block type).

Referential integrity is then code, not DB constraints. Each app declares a **deletion policy** per link kind (RESTRICT / CASCADE / DETACH); before deleting an entity, the core checks incoming links and applies it. This is the functionally riskiest point (today FK RESTRICT guarantees a note can never be broken) — needs serious test coverage.

To settle: exact schema and indexes of `EntityLink`, migration of existing join rows, deletion policy API, and transactional guarantees of the reconciliation (events are in-process today; what happens on partial failure?).

### 4. Bidirectional note ↔ resource coupling

`note_service.py` imports `ResourceModel`/`ViewConfig`/`ScenarioService` (expected direction), but `resource/view_config/view_config_service.py` also imports `NoteViewModel` (reverse direction). Both must go through `EntityLink`: the workflow side queries "incoming links on VIEW:xxx" without knowing notes exist.

### 5. Rich text engine: generic core + app-registered blocks

`impl/rich_text/` stays in the core (it is the cross-app composition point) but must lose all knowledge of app blocks. A registered block provides: payload schema, renderer (e.g. resolve a `view_config_id` into view JSON), reference extractor. Unknown block type ⇒ "unavailable" placeholder, JSON preserved.

To settle: renderer contract (backend enrichment endpoint vs frontend calling each app's API), placeholder UX, and where `fileView` lands (file store is core, but the *view* rendering machinery is workflow).

### 6. `NoteScenario` semantics

Notes are hard-linked to scenarios via the `gws_note_scenario` M2M (auto-maintained from embedded views). Decide whether this is: (a) a note-domain feature ("scenarios this note documents") expressed as an `EntityLink` kind derived from embedded views + optional manual association — preferred; or (b) a workflow-domain feature. Impacts who owns the link kind and its deletion policy.

### 7. App file management vs resources ⚠ (options)

External apps (pattern `gws_project` / `project_document`, also `gws_invest`) manage their own files: a per-brick document table + a brick-owned filestore, outside the resource system. But sometimes the user needs to **analyze** such a file in the lab — it must then already be, or become, a `ResourceModel`.

Technical constraints (current gws_core):
- `ResourceModel.save_from_resource(File(path), origin=ResourceOrigin.UPLOADED)` is the canonical entry point to create a resource outside a scenario (`resource/resource_model.py:516`). It **moves** the file into the resource file store — copy first if the app keeps its own copy.
- `is_symbolic_link` lets an `FSNodeModel` point at a file without owning it (no physical delete on resource deletion), but **only for files already inside the resource file store** — an external path cannot be referenced.
- Store selection is hard-coded to the default (oldest) `LocalFileStore` — no per-brick store in the standard flow.
- **No content dedup**: no checksum on `FSNodeModel`/`ResourceModel`; promoting twice yields two resources.

#### Option 1 — On-demand promotion by copy (document stays app-owned)

The app keeps its filestore + document table. On "analyze": copy to a temp path → `save_from_resource(File(tmp), UPLOADED)` → store the link on the document row (soft `resource_id`, no FK — an `EntityLink` in the target architecture) + a `promoted_content_hash` to skip re-import when unchanged.

- ✅ Full app autonomy (works without `gws_workflow` — consistent with à-la-carte installation); only analyzed files become resources (no explorer pollution); zero gws_core change; pattern already proven (`gws_ai_toolkit` `community_resource_files_manager_service`: promotion + tag-based dedup); the resource is an **immutable snapshot**, which is the expected resource semantics.
- ❌ Storage duplication (two physical copies); divergence if the document is edited afterwards — policy needed (re-promotion = **new** resource, the old one remains the snapshot of the past analysis); deletion semantics to define on both sides; dedup is DIY (content hash as tag or column).

#### Option 2 — Resource-first (the app stores everything as resources)

No app filestore: every uploaded file immediately becomes a `ResourceModel` (`flagged=False` + ownership tags to hide it from lists); the document table only carries a `resource_id`. This is what `gws_ai_toolkit` RAG does (`RagResource` wraps an existing `ResourceModel`).

- ✅ Nothing to import, everything instantly analyzable; single storage (backup, quota, views available); no divergence/dedup between two worlds.
- ❌ **Hard dependency of the app on the resource system** — breaks à-la-carte autonomy (app cannot run without `gws_workflow`); flagging/filtering to manage; constrained lifecycle (a document deleted in the app whose resource is consumed by a scenario cannot be cleaned up freely); every file pays the resource overhead even if never analyzed; single global file store — no per-app isolation or storage accounting.

#### Option 3 — Shared file layer in the core, two façades

The **core** owns the file layer (FileStore/FSNode); apps store their documents there (one store each); promotion copies nothing — create a `ResourceModel` pointing at the existing `FSNodeModel` with `is_symbolic_link=True`.

- ✅ Zero duplication; instant promotion (pure metadata); unified storage infra; most aligned with the modular architecture (core = files, workflow and apps = façades).
- ❌ Requires gws_core evolutions that don't exist today (per-brick store selection; shared file ownership ⇒ refcounting or owner designation for deletion); above all a **mutability problem**: if the app edits the file in place, the resource silently changes while a resource is supposed to be a stable snapshot — needs copy-on-write or an immutability rule for promoted documents. Most elegant, most expensive.

#### Option 4 — Lazy import at analysis time (importer task / file-provider port)

Variant of option 1 triggered from the workflow side: a generic "app document source" task takes a soft `(type, id)` reference and materializes the file as a resource when the scenario runs — in the target architecture, via a "file provider" port each app registers.

- ✅ The user picks the document directly as a scenario input; provenance traced by the task; fits the port/registry system naturally.
- ❌ Same copies and divergence questions as option 1; new infra needed (task + document picker in the workflow front); doesn't cover "I just want this file in my resources" outside a scenario.

#### Recommendation

**Option 1 now, option 4 as its natural extension, option 3 as a long-term target only if storage duplication becomes a real cost.** Note: the file layer moving to the core (point 8) makes option 3 significantly cheaper — re-evaluate this recommendation once point 8 is settled. Concretely on the `project_document` pattern: nullable soft `resource_id` + `promoted_content_hash` on the document row; "Analyze in lab" action reuses the existing resource when the hash is unchanged, otherwise copies to temp → `save_from_resource(..., UPLOADED)` with provenance tags. Assumed policy: a promoted resource is a snapshot — re-promotion creates a new resource; deleting the document never touches the resource. On the day of the split, `resource_id` + tags become `EntityLink(document → resource, kind="promoted_as")` and the promotion action becomes a port registered by `gws_workflow`.

### 8. File vs file resource — the file layer moves to the core ⚠ (decision to take)

The raw file layer is a **common building block, not a workflow concern**: it is extracted from `impl/file/` into the core. This introduces a distinction that does not exist today and whose exact contract must be decided:

- **File (core)**: a physical file managed by the core file layer — `FileStore` + `FSNodeModel` (path, size, store). Any app can store files there (app documents, note attachments…), with no resource semantics attached.
- **File resource (`gws_workflow`)**: the `File`/`Folder` *resource* classes stay in workflow — a `ResourceModel` that wraps a core file (soft reference to an `FSNodeModel`) and adds the resource semantics: views, typing, use as task input/output, immutability expectations.

To decide:
- **Ownership & deletion**: today `FSNodeModel.delete_instance` deletes the physical file unless `is_symbolic_link` — with several owners possible (an app document and a file resource pointing at the same file), this needs refcounting or an explicit owner per file, and the `is_symbolic_link` semantics should be redefined accordingly.
- **Stores**: keep one default store or one store per app (today the default store is hard-coded to the oldest `LocalFileStore` — per-app stores enable isolation and storage accounting).
- **Mutability contract**: a file referenced by a file resource must be stable (resources are snapshots) — immutability rule or copy-on-write when the app edits its document in place.
- **Impact on point 7**: a core-owned file layer makes **option 3 credible** (promotion of an app document into a file resource without any copy — pure metadata), which may change the recommendation there.

### 9. App vs app resource — the app engine moves to the core ⚠ (decision to take)

Same pattern as point 8, applied to the Streamlit/Reflex app framework (`apps/`). Today the engine (`apps_manager.py`, `app_instance.py`, gateway/nginx services, `reflex/`, `streamlit/` runtimes) and `AppResource` (`apps/app_resource.py`, a `ResourceList`) live together in one module: **an app can only exist as a resource**. Target:

- **App engine (core)**: declaring, launching, routing and authenticating an app becomes a core tool with no resource dependency. Any app brick can run its own apps (e.g. a `gws_project`-style Reflex app) without the resource system — **apps that are not resources**.
- **AppResource (`gws_workflow`)**: the resource wrapper stays in workflow and *calls* the core engine — it adds the resource semantics: persistence as a `ResourceModel`, app inputs as sub-resources, generation by a task, versioned app folder.

To decide: the exact engine/wrapper contract (how `AppResource` passes resources as app inputs when the engine is resource-agnostic — probably a generic inputs contract the wrapper fills); auth and sharing rules for non-resource apps; and custom subdomain uniqueness, which is currently checked DB-wide across persisted `AppResource`s only and must cover non-resource apps too.

### 10. Placement of the other shared building blocks (decided)

- **Common building blocks go to the core**: `config/` (`ConfigSpecs`/`ParamSpec` — needed by both workflow task params and form content) and `folder/` (SpaceFolder — used by scenario, note, resource alike).
- **Everything else under `impl/` goes to `gws_workflow`** (`File`/`Folder` resources, Table, agents, and the other resource/task implementations).
- Two extractions required by this rule: the **rich text engine** (`impl/rich_text/` — cross-app composition point) and the **file layer** (`impl/file/` — see point 8) move out of `impl/` into the core before the split. The `fileView` block can then be a core block since files are core-owned.

### 11. Capabilities & frontend degradation

The front (single `lab-front` for now) needs a core endpoint listing installed apps/capabilities to hide absent sections, plus a generic placeholder rendering for unavailable rich text blocks. Micro-frontend split is explicitly out of scope of this plan.

### 12. Database: single DB vs one DB per module ⚠ (decision to take)

Whatever the choice, each brick owns its tables and its `@brick_migration` chain, with **no cross-brick FK** (soft references only) and core migrations that never import app models (today `core/db/migration/migration_0_*.py` imports models from every domain — the historical migrations must be frozen or rewritten defensively).

#### Option A — One single database (`gws_core`, as today)

All bricks create their tables in the same physical DB/schema.

- ✅ No infra change (deployment, backup, `gws db query` tooling unchanged); cross-app read queries remain possible for debugging/reporting; transactions can span apps while everything runs in one process; migration of existing labs is trivial (tables stay where they are).
- ❌ The isolation is purely conventional — nothing physically prevents a cross-brick FK or JOIN from slipping in (must be enforced by architecture tests, point 13); dropping/reinstalling one app leaves its tables mixed with the others; a later split into separate services requires a data migration at that point.

#### Option B — One database per module (core, workflow, note, form)

Each brick gets its own DB/schema via the existing `AbstractDbManager` mechanism (`get_unique_name()` — the multi-DB support already exists, gws_core just never used it for itself).

- ✅ Physical enforcement of the boundaries: cross-app FKs and JOINs are impossible by construction; clean à-la-carte install/uninstall (dropping an app = dropping its DB); per-app storage accounting and backup; the modular monolith → separate services path is already paid for on the data side.
- ❌ No cross-app SQL at all — every cross-domain query (dashboards, entity navigation, `EntityLink` joins with app tables) must go through code, even for debugging; no cross-app transactions (reconciliation listeners must be idempotent and failure-tolerant — reinforces the concerns of point 3); existing labs need a real data migration (moving tables between databases); heavier local/dev setup and tooling (`gws db query --db` per brick, N migration chains to keep coherent).
- **Core base tables (user, tag…)**: FKs toward the core are pervasive (`ModelWithUser` gives every app table `created_by`/`last_modified_by` → `gws_user`; `folder` FKs → SpaceFolder) and a FK cannot cross databases. Approach: the core base tables are **duplicated into each module DB and synchronized** by the core (replication on user/tag/folder create/update events), so local FKs keep working. The sync mechanism is to design: bootstrap copy on app install, idempotent replication events, and acceptance of eventual consistency between DBs.

The `EntityLink` table (point 3) lives in the core DB in both options and never joins app tables directly in option B — which is coherent with its no-FK design.

### 13. Architecture enforcement

Add automated guards so the boundaries survive: import-linter (or equivalent) contracts forbidding app→app imports, CI check, and a test matrix booting the server with each app combination.

### 14. Persisted typing names reference the old brick name

Typing names embed the brick name — `RESOURCE.gws_core.File` (`model/typing_name.py`: `object_type.brick_name.unique_name`) — and are persisted everywhere: `resource_typing_name` on every resource, protocol graphs, scenario templates, kvstore, view configs. Moving `File`, `Table`, tasks, etc. to `gws_workflow` changes their typing name.

**Not considered a blocker: the migration will handle it** — either a data migration rewriting the persisted strings, or an alias mechanism in the `TypingManager` (old typing name → new). To keep in mind when writing the split migrations, including for scenario templates exported/shared between labs.

### 15. Relationship between `gws_workflow` and `gws_note` ⚠ (decision to take)

Some features intrinsically need both apps: `impl/note_resource/` contains **tasks that generate lab notes** (`GenerateLabNote` uses the task framework AND `note/task/lab_note_resource.py`), and there is a `note/task/` folder inside the note module itself. Under a strict "no app imports another app" rule these features have nowhere to live. Two options:

- **Option A — `gws_note` imports `gws_workflow`** (one-way, never the reverse): the note brick can define tasks, note-producing resources, and use views directly. Simpler (the current code mostly keeps working), but notes are no longer installable without workflow — the à-la-carte matrix shrinks (workflow alone, or workflow+note, but no note alone).
- **Option B — strict independence**: neither imports the other; they communicate only through core mechanisms (registries, events, `EntityLink`), and bi-app features (note-generating tasks) move to an optional **integration brick** (e.g. `gws_note_workflow`) that imports both. Full autonomy preserved, at the cost of one more brick and a home to find for every future cross-feature.

The same question will arise for `gws_form` × `gws_workflow` (e.g. a form submission triggering a scenario).

### 16. Downstream brick ecosystem (decided: major version bump)

Every existing brick imports from `gws_core` (`from gws_core import File, Table, task_decorator…`); the split breaks all of them. **Decision: a coordinated major version bump of the ecosystem** — bricks update their imports (and their `settings.json` dependencies) to the new bricks, with a migration guide. No long-lived compatibility facade in `gws_core` (re-exporting app symbols would reintroduce a core→app dependency).

### 17. Core modules that reference domain entities (`share/`, `space/`, `community/`, `external_lab/`)

These modules stay in the core in the current plan but know about domain entities: `ShareLink` is entity-bound, the Space sync sends scenarios/notes, `external_lab` imports resources (`IMPORTED_FROM_LAB`). That is a reverse core→app dependency, forbidden by the golden rule. **How to handle them is still to define** — likely the same registry treatment (shareable entity types, sync providers registered by each app), or moving some of them into their owning app; to settle module by module.

# Centralised Document Management — index, drive & access scopes

> Design document, part of the modular refactor. It builds on
> [modular_apps_split_plan.md](modular_apps_split_plan.md) (the technical enabler: registries,
> events, soft references) and connects to
> [app_discovery_and_activation_plan.md](app_discovery_and_activation_plan.md) (à-la-carte apps,
> the `DocumentSource` provider pattern it sketches for the Search app).
>
> ⚠️ **Amended by [shared_folders_plan.md](shared_folders_plan.md)**, which introduces **option C**
> (a shared folder *grants* read access) and changes this plan on five points: the index `UNIQUE`
> constraint, new `source_type`/`source_id`/`scope_source` columns, the meaning of `folder_id`, the
> `IndexedDocumentModel` upsert, and — most importantly — the claim that the index is fully
> rebuildable from providers. Each is flagged inline below with "**Amended by shared_folders_plan**".

## Purpose

Several apps produce things a user thinks of as **documents**: `gws_workflow` produces resources
from scenarios, `gws_project` produces project documents and attachments, `gws_note` produces
notes. Today each of them stores and lists its own, and **there is no place to search across
them**. The goal is:

- one place to **search every document of the lab**, filtered by name, tag, origin, app, date —
  and later by content. This is the cross-app answer: **search unifies, folders do not**;
- a **drive**: folders and sub-folders the user browses, where they upload and organise **their own**
  documents (see the option A/B discussion — whether other apps' documents can be filed there is the
  one decision still open);
- all of it **without the core ever depending on an app**, so the à-la-carte installability that
  the split plan is built on survives.

The target scale drives most decisions below: **~10 apps at launch, substantially more later**.

---

## What the current code actually looks like

Three findings from reading the existing code; the first two are not mentioned in the other
plans and they change the shape of the solution.

### There are three file storage systems, not one

1. **`FileStore` + `FSNodeModel`** (`impl/file/`) — the resource file store. A table, a store
   abstraction, physical deletion on `delete_instance` unless `is_symbolic_link`.
2. **`RichTextFileService`** (`impl/rich_text/rich_text_file_service.py`) — a **completely
   parallel** store under `data_dir/note/{object_type}/{object_id}/filename`. **No table, no
   `FSNodeModel`, no tags, no index.** This is where every note attachment and figure lives.
   Its `object_type` is a free `str` *by design*, so other bricks can store their files there —
   `gws_project` already does, for its project document images.
3. **Brick-owned file stores** — `gws_project`, `gws_invest`, outside gws_core entirely.

Point 8 of the split plan ("the file layer moves to the core") only addresses #1 and mentions
#3. **#2 is not covered anywhere**, and it is precisely the one holding the documents a user
would most expect to find by searching (note attachments).

### There are three parallel entity-type enums

- `TagEntityType` (`tag/tag_entity_type.py`) — SCENARIO, RESOURCE, VIEW, NOTE, SCENARIO_TEMPLATE,
  NOTE_TEMPLATE, FORM_TEMPLATE, FORM
- `NavigableEntityType` (`entity_navigator/`) — a subset, with a conversion method that **raises**
  for the missing ones (`tag_entity_type.py:48-64`)
- `RichTextObjectType` (`impl/rich_text/rich_text_types.py`) — note, note_template, note_resource

The split plan treats these as two separate items (points 1 and 2). They are **one registry**:
key, model type, human name, navigability, taggability — and now "is it a document". Building
three separate registries redoes the work three times and keeps them free to drift apart, which
they already have.

### There are no per-object permissions in the platform today

`AuthorizationService` does **authentication** (user / app / share link) and never per-object
authorization. `UserGroup` is a flat three-level hierarchy (SYSUSER < ADMIN < USER) compared with
`<`/`<=`. There is **no ACL table, no per-object ownership for rights purposes**. Any lab user
sees everything. `ShareLink` is outbound sharing, not internal access control.

This matters: the access-scope mechanism below is **the first per-object access control in the
platform**. It is deliberately designed so that the core never holds an authorization model of
its own.

---

## Architecture — three layers

The central mistake to avoid is a single central `Document` table that Note / ResourceModel /
ProjectDocument would inherit from or store their data in. That would make the core know each
app's semantics — the exact coupling the whole refactor removes — and would leave orphan rows in
a core table whenever an app is deactivated.

| Layer | Role | Owns the data? |
|---|---|---|
| **Document index** (`gws_document_index`) | search across everything | **No** — a projection, fully rebuildable |
| **Drive** (`gws_document_folder` + drive files) | folders, sub-folders, direct upload — **its own files only** | **Yes**, for its own uploaded files |
| **Apps** (Note, ResourceModel, ProjectDocument…) | business semantics, lifecycle, permissions | **Yes** |

### The index is a projection, never a source of truth

One row per document, keyed by a soft `(entity_type, entity_id)` reference — **no FK**. The note
stays in `gws_note`, the resource in `gws_resource`, the project document in `gws_project`.
Dropping the whole index loses nothing: it is rebuilt by asking every provider to re-enumerate.

That property is what makes the whole design safe, and it is what makes deactivating an app
clean: deactivate = delete its index rows; reactivate = re-enumerate.

⚠️ **Amended by [shared_folders_plan.md](shared_folders_plan.md) — this no longer holds for shared
rows.** Rows with `scope_source = 'SHARED'` cannot be produced by any app's `enumerate()`, because no
app knows about sharing; their source of truth is `gws_shared_folder_item`. **A rebuild that only
replays providers would erase every share in the lab.** The rebuild procedure must re-project the
shares table as well. Everything else in this section stands.

```
gws_document_index                          the real data lives here
├── (NOTE, abc-123, "Rapport mars")      →  gws_note.id = abc-123
├── (RESOURCE, def-456, "resultats.csv") →  gws_resource.id = def-456
└── (PROJECT_DOC, ghi-789, "devis.pdf")  →  gws_project.id = ghi-789
```

A search is **one SQL query** over the index (joined to `gws_entity_tag` for tags), returning the
three mixed, sorted and filtered. Clicking opens the document in its own app.

### The drive owns its own files only (option A — preferred)

> **Status: preferred solution, pending internal validation.** Option B (drive folders holding
> references to *any* app's documents) is kept in "Alternative considered" below, with the arguments
> both ways, so the choice can be discussed internally before it is locked in.

**Decision: a drive folder contains only documents the drive owns** — what the user uploads and
organises by hand. Documents belonging to other apps (resources, project documents, notes) are **not
filed into drive folders**; they are reachable through search, and they live in their own app's
structure.

Two reasons, in order of weight:

1. **Apps have no folder hierarchy to offer.** Each already has a structure suited to its domain, and
   none of them naturally produces a folder tree. `gws_workflow` resources are organised by
   provenance (which scenario, which task, which port) — a scenario producing 50 resources has no
   basis for choosing a folder, and it would be meaningless for it to decide. `gws_project` documents
   are already organised by project and task, and that hierarchy is *the right one for them* —
   duplicating it in the drive would create two competing organisations of the same content.
   `gws_note` uses Space folders (which are themselves slated to disappear). Add volume: thousands of
   auto-generated resources either land in one huge useless "unsorted" folder, or a human files them
   by hand, which does not scale.
2. **A folder whose contents differ per viewer is a bad object.** Under option B a project document
   filed into a shared drive folder keeps its `project:abc` scope, so most people opening that folder
   would not see it. Someone who files ten project documents into a shared folder and finds that
   colleagues see three will read it as a bug — and no UI affordance really fixes that.

What this yields:

- **The drive is just another app**: it owns its files, has its own hierarchy, and its own scope
  `drive_root:<id>`. **A folder therefore looks the same to everyone who can access it.**
- **The cross-app need is met by search**, which was the original request — one place to search
  everything, filtered by name, tag, origin, app. It was the *drive* that additionally claimed to
  organise those documents, and that is the part that did not hold.
- `folder_id` on an index row is meaningful only for drive-owned documents (`owner_app = "DRIVE"`),
  and `NULL` for everything else — no ambiguity.

The drive remains the natural replacement for `RichTextFileService`: note attachments and directly
uploaded files become drive files, and therefore taggable, searchable and shareable.

**What is given up**: gathering documents of mixed origin into one deliverable (three scenario
resources + two project documents + one upload, grouped for a client). Two ways to cover it without
reintroducing the problem: **tags** (already supported, already filterable in search — grouping
without hierarchy), or later an explicit **collection** object referencing documents, whose visibility
is by construction the intersection of the members' access. A collection is more honest than a folder,
because the name does not promise an organisation. Neither is built now; tags cover the need.

⚠️ **Amended by [shared_folders_plan.md](shared_folders_plan.md)**: under option C this is no longer
given up. A folder entry carries its own title, so mixed-origin documents can be gathered *and*
renamed for the recipient — which is what the deliverable use case actually needs.

### Alternative considered: option B — drive folders hold references to any document

Kept for the internal discussion. Under option B, a drive folder contains *index entries* rather than
files, so a scenario-generated resource could be filed into a drive folder without being moved — it is
classification, not storage.

- ✅ It is what the word "drive" intuitively promises; no file duplication; one place that both
  searches *and* organises everything; supports the mixed-origin deliverable use case directly.
- ❌ The two objections above: apps have no coherent hierarchy to contribute, and folders become
  heterogeneous in visibility.
- ❌ It needs a **precedence rule** that option A does not: a document filed in a drive folder is
  subject both to "the folder organises, the app authorises" and to `drive_root:<id>` inheritance.
  Applying the drive scope would *widen* access to a confidential document — the vulnerability
  explicitly rejected under access scopes — so the owning app's scope must always win, and
  `drive_root:<id>` must apply only to `owner_app = "DRIVE"`.
- ❌ It needs **two distinct verbs** in the UI: "remove from folder" (`folder_id = NULL`) for another
  app's document versus "delete" for a drive-owned one — deleting from the drive must never be able to
  destroy a project document.
- ❌ It needs UI mitigations that only soften the symptom: warn at filing time ("this document stays
  visible only to members of project X") and show an owner chip (Project / Workflow / Drive) on every
  item.

If option B is chosen, the four bullets above are requirements, not details, and the "one folder per
document" simplification also becomes questionable: filing one document under two roots would give it
two perimeters, contradicting the "exactly one perimeter tag" rule.

### Option C — the shared folder *grants* access (see shared_folders_plan.md)

Detailed in [shared_folders_plan.md](shared_folders_plan.md); summarised here so the three options can
be compared in one place.

Options A and B both assume **the folder classifies, the app authorizes** — filing a document into a
shared folder gives nobody access. Option C inverts that: **filing grants `READ`**, creating a second
access path alongside the owning app's (`app_access OR shared_access`, capped at read).

- ✅ **Objection 2 to option B does not apply.** A granting folder shows the same contents to every
  member, so the "folder that differs per viewer" problem disappears — C is *better* than A on this
  criterion, not worse.
- ✅ **Objection 1 does not apply either.** Nothing is filed automatically: a human deliberately shares
  a handful of objects. No app is asked to place its 50 generated resources, so the volume argument is
  moot.
- ✅ Covers the **mixed-origin deliverable** use case this plan gives up under option A (see "What is
  given up"), because a folder entry carries its own title.
- ⚠️ It introduces the platform's **first second access path**, and with it the folder entry as an
  object of its own (own id, own title, own tags, borrowed content).
- ⚠️ It requires the schema and rebuildability amendments flagged in this document.

**Do not reject C by assimilation to B** — they differ on exactly the point that made B unacceptable.

### Drive sharing: root folders only (settled, V1)

Under option A the drive owns only its own uploads, so this section governs exactly those. Direct
uploads have no app behind them to authorise, so the drive must decide, and creator-plus-admin
(`is_private`) is too poor for "share this with Marie and Paul". (Under option B this section would
additionally need the precedence rule listed in "Alternative considered": the owning app's scope always
wins, and `drive_root:<id>` applies only to `owner_app = "DRIVE"`.)

**Decision: only a root folder is shareable. Sub-folders inherit from their root and cannot be shared
individually.**

```
access_scope = "drive_root:<root_folder_id>"
```

Why this shape rather than full per-folder inheritance: the scope stays a **flat string compared by
equality**, exactly like `project:abc`. The `gws_user_scope` join, the index query and the RAG chunk
metadata are all unchanged. Full inheritance would make a document's scope depend on its whole parent
chain, so moving a folder near the top of the tree would invalidate the scope of every descendant —
thousands of index rows to rewrite plus a RAG metadata propagation. With a single shareable level,
each tree has exactly one source of truth and no variable depth.

Rules:

- **One personal root per user.** A draft goes in the user's own unshared root, which makes a separate
  `is_private` flag unnecessary — one mechanism instead of two.
- **Sharing is with individual users in V1.** `UserGroup` is a three-level hierarchy
  (SYSUSER/ADMIN/USER), not named groups, so there is nothing to share *with* yet. At the scale of
  roots (tens, not thousands) a per-root user list is acceptable — this is the one place where the poor
  solution is accepted knowingly. Named groups are a prerequisite for anything richer.
- **Moving a sub-tree between roots changes the scope of every descendant document.** Rare and
  explicit, so it may be slow, but it must be transactional and must emit the "perimeter changed"
  event for all affected documents (see the RAG access-control section). Promoting a sub-folder to a
  new root is the same case.
- **The UI must state that sharing lives at the root level** — not merely disable the button
  elsewhere. A user who can share a root will try to share a sub-folder within the week, and a
  permission model that surprises is a permission model that leaks.

Rejected alternative: per-folder scopes **without** inheritance. Technically the cleanest (one
indirection, no cascade on move), but creating a sub-folder inside a private folder would yield a
public sub-folder — a leak by misunderstanding, since the intuition of inheritance is too strong to
contradict.

⚠️ **Migration path to full inheritance**, to note now while the reasoning is fresh: it requires a
**hierarchical scope** (`drive:/a/b/%` matched with `LIKE`, backed by the folder's `path_cache`)
instead of a flat one — so a migration of every index row *and* all RAG chunk metadata. Deciding the
scope's nature later is expensive; this is why the flat form is a deliberate V1 choice rather than an
oversight. `path_cache` already exists in the schema for this, and a hierarchical scope is also the
escape hatch listed for scope volume.

---

## How the index is written

### Providers, and a mixin for the common case

Each app registers a `DocumentProvider` at brick load time. The core never knows `Note`; it only
knows this contract.

```python
class DocumentProvider(ABC):
    entity_type: str                                    # "RESOURCE" | "NOTE" | "PROJECT_DOCUMENT"

    def enumerate(self, since) -> Iterable[DocumentDescriptor]: ...   # rebuild / catch-up
    def get_descriptor(self, entity_id) -> DocumentDescriptor: ...
    def open_content(self, entity_id) -> IO | None: ...  # for future full-text indexing
    def get_route(self, entity_id) -> str                # deep link into the app
```

But **apps almost never call the index service explicitly**. A model that inherits
`IndexedDocumentModel` is indexed in `save()` and de-indexed in `delete_instance()`:

```python
class ProjectDocument(IndexedDocumentModel):
    entity_type = "PROJECT_DOCUMENT"

    def get_document_descriptor(self) -> DocumentDescriptor:
        return DocumentDescriptor(title=self.name, origin=..., fs_node_id=...)
```

This is the pattern already used by `ModelWithUser` (fills `created_by`/`last_modified_by`) and
`ModelWithFolder`. A third mixin of the same family.

⚠️ **Amended by [shared_folders_plan.md](shared_folders_plan.md)**: the mixin's upsert must target the
`scope_source = 'OWNER'` row only. An upsert keyed on `(entity_type, entity_id)` alone would overwrite
or duplicate the entity's share rows on every save.

The provider is then only needed for what the mixin cannot do: **rebuilding** the index,
**entities that cannot inherit the mixin** (`ResourceModel` already inherits three base classes,
and not every resource should be indexed), and **reading content** for future full-text search.

### Direct call, not events — and in the same transaction

**Decision: the app calls the core (through the mixin), it does not emit an event.**

Events are the right tool when the emitter must not know anyone is listening — as in
`form_note_join_listener`, where the form is unaware notes exist. That is not the case here: the
app *wants* its document indexed. It is a core service it deliberately consumes, like
`EntityTagList` or the file store. Nothing to decouple.

The direct call gives three things an event does not:

- **Transactionality** — the index row is written in the same transaction as the document. Either
  both exist or neither. A partially-failing in-process listener is exactly the concern raised in
  point 3 of the split plan.
- **Typing** — a checked signature instead of a string event name and a runtime-only payload.
- **Debuggability** — a readable call stack instead of an invisible listener.

An app calling the core is the one import direction the golden rule allows, so no architectural
rule is bent.

**Not at the file-store level.** The file store only knows bytes — not that a file is project
document `ghi-789`, nor its business title or origin. And not every document has a file (a note
has none), so that level could never cover notes.

### Reconciliation

Events/mixin cover the nominal path; a periodic reconciliation replays `enumerate()` to catch
what was missed. `source_version` (the source's `last_modified_at` at indexing time) lets it
detect stale rows without re-reading every document.

Physical consistency stays a concern: a file deleted from disk outside the model leaves a
dangling index row. That is already true of `FSNodeModel` today; reconciliation is what catches it.

---

## Access scopes

### The problem

Each app has its own — legitimately different — access model:

- **`gws_project`**: access by project membership. Per-row, varies per user.
- **`gws_workflow`**: access to the app means access to everything in it. Binary.

These are not reconcilable in a central table, and **they should not be**. Who may access a
project is `gws_project` business logic. The core has no legitimacy to know it, and knowing it
would make the core depend on the app.

So the question is not "what permission model for the drive", but **"how does the drive respect
rules it does not know"**.

### The mechanism: opaque scopes, carried by a system tag

Each document carries **exactly one perimeter tag**, set by its app — e.g.
`gws_project:mon_project`. Other tags (`app:project`, `gws_task:ma_task`) stay purely business.

Tags are the right carrier here — not "just metadata" in this system: `TagOriginType.SYSTEM`
exists and `tag_service.py:411-412` refuses deletion of any tag whose origin is not a user, so
immutability is enforced by the system, not by convention. Propagation is opt-in
(`is_propagable`). And the tag will be set anyway for business reasons, so a parallel
`visibility_scope` column would be pure duplication of the same fact.

The index **derives** a queryable column from that tag, in the same transaction:

```
access_scope     -- NOT NULL, indexed, derived from the perimeter tag
owner_app        -- "PROJECT" | "WORKFLOW" | "DRIVE"
```

Why derive a column rather than filter on tags directly — the difference is not where the
information is stored, it is **what happens when it is missing**:

- `NOT NULL` makes a document without a perimeter impossible to insert. A missing tag is silent.
- The filter lives **inside the index's own search builder**, so it cannot be forgotten by a
  caller writing a new query. `EntityWithTagSearchBuilder.add_tag_filter` must be called
  explicitly; forgetting it on a business filter returns too many rows (annoying), forgetting it
  on a security filter returns **every document** (a leak). The failure modes are not symmetric.
- Index scan instead of one join per criterion (`entity_with_tag_search_builder.py:74-91`) on the
  drive's most frequent query.

The core never learns what `project:abc` means. It composes scopes it does not understand.

### `gws_user_scope` — required, not an optimisation

A first draft of this design resolved scopes per request by calling
`get_visibility_scopes(user)` on each active app. **At the target scale that does not hold**, for
two reasons — the second being the decisive one:

1. Every search would call all ~10 (then ~50) apps, several of which query their own tables. The
   search latency becomes the *sum* of all installed apps' latencies, and one slow or failing app
   breaks a search that did not concern it.
2. The composed `WHERE` clause **changes shape with the number of installed apps**:

   ```sql
   WHERE (owner_app='PROJECT'  AND access_scope IN (...))
      OR (owner_app='WORKFLOW' AND access_scope='*')
      ... × 50
   ```

   MariaDB's optimiser degrades badly on a disjunction that size. A join does not change shape at
   all:

   ```sql
   JOIN gws_user_scope us ON us.scope = di.access_scope AND us.user_id = ?
   ```

So `gws_user_scope(user_id, scope, owner_app)` is part of the design from the start. **But it is
a rebuildable cache, never a source of truth** — the same discipline as the document index, of
which it is effectively a second projection.

Rules, all of which must be explicit because this is the one place where staleness is a security
incident rather than a display glitch:

- **Maintained through a core API** (`grant(user, scope)` / `revoke(user, scope)`), not by each
  brick writing the table itself. At 50 apps, one of them will get it wrong, and that one is a
  leak.
- **`revoke` is synchronous and transactional, never queued.** Granting late is benign; revoking
  late is a leak. The asymmetry is a rule, not an implementation detail.
- **Rebuildable at any time** from the providers, with periodic reconciliation.
- **Fail closed**: an app whose scopes are unavailable or stale must drop *its* results, never
  open by default and never break the whole search.
- A stale `access_scope` (a document moved between projects) is likewise a security incident —
  hence writing it in the same transaction as the app-side change.

This table is the most sensitive component of the design: a security index on the path of every
search. It deserves dedicated tests on revocation, auditability of writes, and a documented
rebuild procedure.

### What is explicitly not in scope

`gws_core` still has no per-object permissions for notes and resources. The drive does not fill
that gap — those providers expose `*`. The day gws_core gains real permissions, only the
provider concerned changes.

---

## Schema

```sql
gws_document_folder(
    id, name, parent_id, path_cache,
    is_root,                             -- only a root folder is shareable (see drive sharing)
    root_folder_id,                      -- denormalised: the tree's root, source of the scope
    created_by, last_modified_by, created_at, last_modified_at
)

-- V1 sharing: who may see a root folder's tree. No named groups exist yet (UserGroup is a
-- three-level hierarchy), so this lists individual users; acceptable at the scale of roots.
gws_document_folder_share(root_folder_id, user_id)   -- UNIQUE together

gws_document_index(
    id,

    -- identity: soft reference, NO FK. Same keys as EntityTag → taggable for free
    -- ⚠ Amended by shared_folders_plan: this identifies THIS ROW, not the referenced entity.
    -- On a SHARED row it is (FOLDER_ITEM, <entry id>) so the entry is taggable independently.
    entity_type, entity_id,

    -- ⚠ Added by shared_folders_plan: the referenced entity. NULL on an OWNER row.
    source_type NULL, source_id NULL,    -- UNIQUE (source_type, source_id, access_scope)
    scope_source,                        -- 'OWNER' | 'SHARED' (see below: required, not cosmetic)

    -- what the user sees and searches
    -- on a SHARED row, title is the ENTRY's own title, independent from the source's and never
    -- synced; the source title is deliberately NOT searchable through the entry
    title,
    mime_type NULL, extension NULL, size NULL,

    -- origin (see "points to settle": the vocabulary must be fixed)
    origin_type,                         -- UPLOAD | GENERATED | IMPORTED | AUTHORED | DERIVED
    origin_id NULL, origin_entity_type NULL,

    -- drive classification (NOT SpaceFolder)
    -- ⚠ Amended by shared_folders_plan: no longer meaningful only for owner_app = "DRIVE";
    -- it is set on every SHARED row (the folder the entry sits in)
    folder_id NULL,

    -- access control
    owner_app,
    access_scope,                        -- NOT NULL, derived from the perimeter tag

    -- ownership
    created_by, last_modified_by, created_at, last_modified_at,

    -- physical file
    fs_node_id NULL,                     -- FK FSNodeModel if in the core file store
    storage_ref NULL,                    -- opaque key for stores outside the core file store
    content_hash NULL,

    -- state
    is_archived, is_deleted, is_validated NULL,

    -- index mechanics
    indexed_at, content_indexed_at NULL, source_version NULL
)

gws_user_scope(user_id, scope, owner_app)   -- rebuildable cache, see above

-- phase 2, deliberately a separate table: LONGTEXT in the main table would weigh down
-- every metadata scan, and these columns serve only full-text queries
gws_document_content(document_id, content_preview, content_text)
```

Indexes:

```
UNIQUE (entity_type, entity_id)         -- ⚠ amended: identity of the row
UNIQUE (source_type, source_id, access_scope)   -- ⚠ added: one entry per source per root scope
INDEX  (source_type, source_id)         -- ⚠ added: find every row referencing an entity
INDEX  (owner_app, access_scope)        -- the security filter, on every query
INDEX  (title)
INDEX  (entity_type, last_modified_at)  -- per-app listing, most recent first
INDEX  (folder_id)
INDEX  (origin_type, origin_id)
INDEX  (content_hash)
INDEX  (indexed_at)                     -- reconciliation sweep
gws_user_scope: INDEX (user_id, scope), INDEX (scope)
```

Notes on specific choices:

- **No `SpaceFolder` FK** — SpaceFolder may disappear. `Note` and `ResourceModel` still carry
  their own `folder` FK today; removing it is a separate piece of work, a dependency of this
  plan rather than an assumption of it.
- **No denormalised tag columns.** Tags live in `EntityTag` only. Filtering joins
  `gws_entity_tag`, which already stores the same `(entity_type, entity_id)` keys, so tagging a
  document requires **no new code at all**. Denormalisation can be revisited if measurements ask
  for it.
- **`fs_node_id` nullable** is what makes the index shippable *before* point 8 (the file layer
  moving to the core) is settled. `storage_ref` covers `RichTextFileService` and brick-owned
  stores while they exist.
- **`is_deleted` (soft delete)** rather than a hard DELETE, so deactivating an app does not lose
  indexing history. Cost: every query must filter it — hence encapsulating it in a dedicated
  search builder, as `note_search_builder.py` already does for notes.

---

## Impact on the split plan

- **Point 1 (tags as registered types)** and **point 2 (generic navigation)**: merge into a
  single entity registry, which this plan needs anyway (the index must know entity types, and
  `TagEntityType` must accept the new ones).
- **Point 7 (app files vs resources)**: unchanged recommendation (option 1, promotion by copy).
  This plan adds the back-link as an index row rather than an ad-hoc column.
- **Point 8 (file layer to the core)**: must additionally cover `RichTextFileService`, which no
  plan currently mentions. **The index does not depend on point 8** — it indexes descriptors, not
  bytes.
- **`EntityWithTagSearchBuilder` takes a single `entity_type`** (`entity_with_tag_search_builder.py:24-30`).
  A cross-app search needs several at once — a small widening, or a dedicated builder.

---

## Structured entities, not only documents

Not everything worth searching or feeding to a RAG is a document. `gws_project.Task` has a title, a
rich-text `description`, a status, dates, a priority, an assignee, a project, subtasks, progress
(`gws_project/task/task.py`). A note has no file; a task has neither file nor document semantics.

**Do not serialise the object into text.** A `to_text()` dump ("Status: DOING, Priority: HIGH…") makes
a RAG answer *badly* on the structured parts: "how many tasks are late?", "which tasks are assigned to
Marie?" are SQL questions, not similarity questions. Embeddings cannot count, and `HIGH` vs `MEDIUM`
has no order in vector space. The result looks right on vague questions and is wrong on precise ones —
the worst failure mode, because it is invisible.

**Split the two natures of the same object:**

| Part | Example fields | Right tool |
|---|---|---|
| Structured | status, dates, priority, assignee, progress | SQL, via the agent's MCP `db_query` |
| Narrative | `description` (rich text), comments | RAG embeddings |

The structured half already has its tool: the planned agent is wired to the lab MCP server exposing
read-only `db_query` ([ai_agent_chat_plan.md](ai_agent_chat_plan.md)). So **the RAG indexes the
narrative, the agent queries the structured part in SQL, and the agent joins them.** "Which late tasks
concern patient data analysis?" → `db_query` for `end_date < today AND status != DONE`, then
`search_knowledge` for the semantic part, then cross-reference. Each tool does what it is good at.

Two provider methods carry this, for entities where `is_document = false`:

```python
def to_rag_text(self, entity_id) -> str | None:      # narrative; None = nothing indexable
def to_rag_metadata(self, entity_id) -> dict:        # structured fields, as chunk metadata
```

Pitfalls, all three real:

- **Re-indexing frequency.** A `Task` is saved many times a day. Re-indexing must be driven by a hash
  of the **extracted narrative text**, not `last_modified_at` and not the DB row — otherwise every
  status change pays an embedding call. This is a genuine difference from documents, which change
  rarely.
- **Entities with no narrative.** An empty `description` means `to_rag_text()` returns `None` and the
  row is skipped — otherwise the vector space fills with three-word titles that match everything and
  inform nothing.
- **Granularity.** One entity = one RAG document; relations ride in metadata (`parent_task_id`) and the
  agent walks the tree in SQL when needed. A task tree as a single document was considered and
  rejected as harder to retrieve precisely.

---

## RAG integration

**Direction: the RAG reads the index. No app ever pushes to the RAG.**

`gws_ai_toolkit` implements **one** provider (`document_index`) instead of one per app, and its
`sync_config` becomes a query over the index ("tagged `projet:X`", "drive folder Y"). Any app that
indexes becomes RAG-able with no change in `gws_ai_toolkit`.

This dissolves that plan's blocking "Open decision"
(`rag_embedded_stack_implementation_plan.md:7-34`): the question "should the `resource` provider ship
in `gws_ai_toolkit` or be registered by `gws_workflow`?" disappears — there is no `resource` provider
at all.

**Admin upload goes through the drive**, then the RAG picks it up from the index — one write path.
This removes `add_uploaded_document` and the built-in `upload` provider from that plan, and makes
RAG-uploaded files taggable, searchable and scope-filtered like anything else instead of being locked
inside the RAG.

**Hash instead of snapshot.** That plan snapshots every document into the brick filestore and indexes
only the snapshot (`:274-276`). Replaced by `content_hash`: the **chunks in LanceDB are the persisted
data**; the binary snapshot only ever protected re-indexing after the source vanished — and
re-indexing a deleted document reconstructs data that should be gone. Effects: `snapshot_path` →
`content_hash`; the disk layout loses `files/<dataset_id>/`; `get_version_marker` becomes the hash,
more reliable than `last_modified_at` (a no-op save stops triggering re-indexing). This is also what
makes structured-entity indexing affordable.

Accepted consequence: `open_document` can no longer download a local copy — it deep-links into the
owning app, which is better (the user sees the live document) but needs a "source unavailable" state
when the source is gone, with chunks still displayable since they live in LanceDB.

**Deletion is event-driven and immediate.** Deleting chunks is a metadata-predicate `DELETE` in
LanceDB — no LLM call, no embedding, essentially free. Same asymmetry as access scopes: deletion
synchronous, addition may be deferred. Periodic sync stays as the safety net.

⚠️ **Implementation constraint:** this crosses a brick boundary (index in the core, LanceDB in
`gws_ai_toolkit`) and LanceDB enforces a single-writer rule — all writes happen in the Reflex app
process (`:475-478`). A core-side listener therefore **cannot** delete chunks directly: it must
enqueue deletions in a DB table the RAG process consumes. This is a real constraint, not a detail.

### Access control inside the RAG ⚠

`access_scope` must travel into the chunk metadata — a RAG returning excerpts from projects the user
cannot access is a leak. Mechanically this works: the RAG plan already excludes metadata from the
embedded text (`:99-100`) and LanceDB filters on it via `MetadataFilters` (`:106-107`), so filtering
happens inside the vector engine with no post-filtering.

**But metadata is a frozen copy, and that is not sufficient on its own.** The scope written into a
chunk dates from indexing time. If a document's perimeter changes (moved to another project), the
chunk keeps the old scope until re-indexing — and re-indexing is driven by the *narrative text* hash,
which a perimeter change does not affect. So the stale scope would persist **indefinitely**: the
document changed project, but the RAG keeps serving it to the former project's members.

Two complementary mechanisms — the first corrects, the second guarantees:

1. **Two distinct triggers (the nominal path).** Text change → full re-index (chunks + embeddings,
   expensive). Perimeter change → **metadata-only update** of the document's chunks (no embedding
   call, as cheap as deletion). The index emits *two* events — "content changed" and "perimeter
   changed"; the second matters most for security and costs least to handle. This is what keeps chunk
   metadata current and lets `MetadataFilters` do the filtering inside the engine.
2. **SQL verification of retrieved ids (the backstop).** After retrieval, check the returned
   `document_id`s against the index (authoritative, `NOT NULL` scope) before building the answer.

Why (2) is kept even though (1) exists — the update cannot be applied *directly* from the event.
LanceDB's single-writer rule means all writes happen in the Reflex app process (`:475-478`), while the
listener runs in the server process: the update necessarily goes through a queue consumed by another
process, so metadata synchronisation is **asynchronous by construction, not by design choice**. Three
failure modes the queue does not cover, all sharing the same symptom — *the RAG answers, with the old
perimeter, with no error and no log*:

- **The RAG process is stopped or crashed.** The queue backs up while LanceDB keeps serving reads
  (reads need no writer), so answers carry stale scopes indefinitely.
- **An update fails silently** after the queue was consumed.
- **Deployment**: a restart with events in flight, or a migration, can lose the queue.

Cost of (2): one indexed `IN` query on a handful of ids, once per answer — invisible next to query
embedding plus the LLM call. It buys correctness that no longer depends on another process being
healthy, which is the difference between "correct when all goes well" and "correct". Dropping it would
require, at minimum, an alert on queue age plus a fail-closed refusal to answer on stale metadata —
more machinery than the query it replaces.

The pure alternative — no scope in LanceDB, filter everything post-retrieval against SQL — never goes
stale but forces over-fetching, and makes the effective `top_k` unpredictable (if the best 5 chunks are
all inaccessible, the user gets nothing even though the 6th was accessible). Hence: **metadata for
filtering, SQL verification as the guarantee.**

---

## Settled: origin vocabulary

`origin_type` answers **one question only — how did this document come to exist?** The *where* lives
in `(origin_entity_type, origin_id)`, which is what makes the scheme extensible without touching the
enum. `ResourceOrigin` could not be generalised as-is because it mixes the two dimensions
(`UPLOADED`/`GENERATED` are a "how", `IMPORTED_FROM_LAB`/`S3_FOLDER_STORAGE` are a "where").

| Value | Meaning | Examples |
|---|---|---|
| `UPLOADED` | a human supplied the file | drive upload, `ResourceOrigin.UPLOADED`, attachment |
| `AUTHORED` | a human wrote it inside the lab | note, task description |
| `GENERATED` | an automated process produced it | scenario resource, generated report |
| `IMPORTED` | came from an external system | `IMPORTED_FROM_LAB`, `S3_FOLDER_STORAGE`, sync |
| `DERIVED` | derived from another lab document | promotion to resource, format conversion |

Mapping from what exists today:

```
ResourceOrigin.UPLOADED          → UPLOADED
ResourceOrigin.GENERATED         → GENERATED + origin=(SCENARIO, scenario_id)
ResourceOrigin.IMPORTED_FROM_LAB → IMPORTED  + origin=(EXTERNAL_LAB, lab_id)
ResourceOrigin.S3_FOLDER_STORAGE → IMPORTED  + origin=(S3, bucket)
Note                             → AUTHORED  + origin=(USER, created_by)
ProjectDocument (upload)         → UPLOADED
Promotion document → resource    → DERIVED   + origin=(PROJECT_DOCUMENT, doc_id)
```

Inclusion criterion: **would a user filter on it?** "Show me what I uploaded", "what the scenarios
produced", "what came from outside" — yes. A value that never serves as a filter belongs in
`origin_entity_type`, not in this enum.

Remaining judgement call: `AUTHORED` vs `UPLOADED` for a note. `AUTHORED` is kept because
"written here" vs "brought in from outside" is the distinction that matters to someone searching; if
that proves useless in practice, merging the two loses little.

## Settled: one entity-type registry replaces five enums

Reading the code turned up **five** parallel enumerations of the same entities, not the three the
split plan mentions (its points 1 and 2):

| Enum | Values | What it adds |
|---|---|---|
| `TagEntityType` | 8 | taggability + `get_entity_model_type()` |
| `NavigableEntityType` | 6 | navigation + human name |
| `RichTextObjectType` | 3 (`str`, **lowercase**) | rich text file storage |
| `ActivityObjectType` | 7 (incl. `PROCESS`, `USER` — nowhere else) | activity log |
| `ShareLinkEntityType` | 2 | sharing |

None is a proper subset of another: `NavigableEntityType` lacks `SCENARIO_TEMPLATE`/`NOTE_TEMPLATE`,
`ActivityObjectType` alone has `PROCESS`/`USER`, and `RichTextObjectType` uses lowercase (`"note"`)
where the others use uppercase (`"NOTE"`).

**Decision: one registry, with declared capabilities** — one entry per entity type, registered by its
owning app at brick load:

```python
@entity_type_decorator(
    key="NOTE",                    # ⚠ persisted value — never change
    model=Note,
    human_name="Note",
    taggable=True,
    navigable=True,
    shareable=False,
    indexable=True,                # new: enters the document index
    rich_text_storage="note",      # the historical lowercase value, preserved as-is
    activity_logged=True,
)
class NoteEntityType(EntityTypeDefinition):
    def get_navigation_previous(self, entity_id): ...
    def get_navigation_next(self, entity_id): ...
```

The five consumers then query the registry (`registry.taggable_types()`, `registry.get(key).model`)
instead of their own enum.

Why capabilities rather than five registries: the five enums answer different questions about the
**same** object. A `Note` is taggable, navigable, indexable, activity-logged, not shareable. Five
separate lists means five places to keep consistent — and `tag_entity_type.py:48-64` already shows the
result: a conversion that **raises** for types missing from the other enum. With capability flags the
inconsistency becomes impossible: a type absent from `taggable_types()` is not an error, it is simply
not taggable.

Hard constraints:

- **Persisted keys are untouchable.** `"NOTE"` is in `gws_entity_tag.entity_type`; `"note"` is in
  rich-text file paths on disk. The registry carries **both** (`key` + `rich_text_storage`) rather
  than unifying the case — unifying would need a data *and* disk-path migration for a purely cosmetic
  gain.
- **`PROCESS` and `USER` stay in the registry** even though they are only activity-logged; excluding
  them would recreate a parallel list.
- **Migration order**: start with `TagEntityType` (most used, and what the index needs), then move the
  four other consumers one at a time. Each enum can survive temporarily as a façade delegating to the
  registry, so nothing breaks at once.

⚠️ **Scope warning**: this is a **bigger job than the index itself** — five consumers, including
`entity_navigator`, which the split plan calls its #1 coupling hub. It likely deserves its own plan
document; it is listed here because the index cannot start without it.

## Points to settle

1. **Drive scope: option A vs option B vs option C** — option A (drive owns only its own files) is
   written above as the preferred solution; option B is documented alongside it; **option C**
   (the shared folder grants read access, see [shared_folders_plan.md](shared_folders_plan.md)) was
   added afterwards and is the one being pursued. **This is the one decision still to validate**, and
   it changes the drive's UI and the meaning of `folder_id`; under option C it also changes the index
   schema, but not the scope mechanism itself.
2. **Multi-folder filing.** One folder per document to start; a link table if the need appears. Under
   option A this is a minor drive feature; under option B, filing one document under two roots would
   give it two perimeters, contradicting the "exactly one perimeter tag" rule. Under option C it is
   natural: two folders means two entries, each with its own scope and title.
3. **Named groups.** Root sharing lists individual users in V1 because named groups do not exist.
   Anything richer (per-folder sharing, org-wide shares) needs them first — a core-level decision
   beyond this plan.
4. **Full-text content.** Phase 2. MariaDB `FULLTEXT` for exact search, or delegation to
   `gws_search` for semantic search — `open_content()` is the only hook needed either way.
5. **Scope volume.** Watch the number of scopes per user; the design assumes membership in tens,
   not thousands, of projects. A hierarchical scope (`org:X/project:abc`, enabling
   `LIKE 'org:X/%'`) is the escape hatch if that assumption breaks. Under option C, shared folders add
   one scope per root a user belongs to — same order of magnitude, but worth counting together.
6. **UI for partially visible folders** — *moot under option A* (a drive folder holds only drive files,
   all sharing one scope, so it looks the same to everyone who can open it). Becomes a requirement if
   option B is chosen: warn at filing time and show an owner chip per item. *Also moot under option C*,
   for the same reason as A: a granting folder shows the same contents to every member.
7. **Structured entities: same table or a sibling?** `is_document` as a discriminant is assumed here,
   which keeps search and scoping shared. But a task is not a document and has no business in a drive
   folder — revisit if the drive UI gets complicated. Under option C a task *can* legitimately sit in a
   shared folder, which weakens the argument for a sibling table.
8. **RAG deletion window.** A document deleted from the drive stays queryable until the deletion
   event lands. Acceptable for a stale document; not for one deleted *because* it was confidential.
   Event-driven deletion closes this, but the failure mode should be documented rather than assumed
   away.
9. **Multi-lab workspaces (unexplored).** The activation plan allows a workspace to span several
   datalabs, with soft references and registries resolved over a lab-to-lab transport
   (`app_discovery_and_activation_plan.md:336-351`). A **per-lab** index does not answer "all my
   documents" at workspace scale — that likely needs a workspace-level aggregation, exactly like the
   capabilities view. Not addressed by this plan, and the only open point that could change the index's
   *shape* rather than its details. Worth a dedicated pass if multi-lab is a near-term goal.
10. **One DB vs one DB per module (split plan point 12).** In the per-module option, `gws_document_index`
    sits in the core DB while referencing entities in other DBs — consistent with its no-FK design, but
    the `folder_id` reference and the `gws_entity_tag` join need verification in that scenario. Not done.
11. **Expected volume (unmeasured).** The whole design assumes tens of scopes per user; 10k vs 10M
    documents also changes indexing and full-text choices. No measurement exists yet.

### Deferred to other refactors (not blocking this plan)

- **Which resources are indexed** — a `Table` or `PlotlyResource` has no `FSNodeModel`; indexing every
  resource makes document search noisy, indexing only file-backed ones excludes things users consider
  deliverables. **Decided during the `gws_workflow` app refactor**, when the workflow provider is
  written. Suggested default meanwhile: filter on file-backed and/or `flagged`, configurable.
  ⚠️ **Amended by [shared_folders_plan.md](shared_folders_plan.md)**: under option C a share *is* an
  index row, so an entity must be indexable to be shareable. This is no longer only about search noise
  — **it gates what can be shared**, which promotes the decision out of "deferred".
- **`RichTextFileService`'s fate** — replacing it with drive files is the most invasive change in this
  plan (data migration + persisted rich text blocks referencing bare `filename`s + `gws_project`
  already using the service), and the only one that makes note attachments genuinely searchable.
  **Decided during the `gws_note` app refactor.** Until then note attachments stay unsearchable (the
  status quo); `storage_ref` in the index schema is what keeps them representable meanwhile.

---

## Sequencing

Steps 0–2 need no brick split: the registry works inside the current monolith and becomes the
cross-brick extension point on split day. This mirrors the activation plan's phase 1, which
works against existing labs.

0. **Entity-type registry** (prerequisite, see "Settled" above) — start with `TagEntityType`, the
   other four consumers following one at a time behind façades. Bigger than the index itself and
   probably its own plan document, but nothing here can start without it.
1. **Contract** — `DocumentProvider`, `DocumentDescriptor`, `IndexedDocumentModel`, core
   registry. Pure code, no DB, no migration.
2. **One real provider** (`ResourceModel`) + an index rebuild command. Validates the model on
   real data before committing other apps to it.
3. **Index table** + mixin + reconciliation. Search by name / tag / origin through
   `SearchBuilder`.
4. **Access scopes** — perimeter tag, `access_scope`, `gws_user_scope`, fail-closed search
   builder. Needed as soon as a second app with a real perimeter (`gws_project`) is indexed.
5. **Drive** — folders, upload, filing. Builds on the index; the index is useful without it, the
   reverse is not true. Under option C this step merges with steps 3–4 of
   [shared_folders_plan.md](shared_folders_plan.md), which shares the same folder tables.
6. **Other providers** — Note, ProjectDocument.
7. **RAG integration** — the single `document_index` provider in `gws_ai_toolkit`, the chunk
   deletion/metadata-update queue, and the two triggers (content vs perimeter) with SQL verification of
   retrieved ids.
8. **Structured entities** — `to_rag_text` / `to_rag_metadata`, starting with `gws_project.Task`.
9. **Full-text content** — only if usage asks for it.

---

## Unrelated bug found while writing this

`note.py:135` — `Note.delete_instance` deletes tags with `TagEntityType.VIEW` instead of `NOTE`:

```python
EntityTagList.delete_by_entity(TagEntityType.VIEW, self.id)
```

Deleted notes therefore leave orphan tag rows, and a note's own tags are never cleaned up. Independent
of this refactor, but it pollutes any tag-based search — and it is exactly the class of error the
unified entity-type registry (point 11) would make impossible by construction.

# Shared Folders & Unified Access Rights

> Design document, part of the modular refactor. It builds on
> [modular_apps_split_plan.md](modular_apps_split_plan.md) (registries, soft references) and
> **amends** [document_management_plan.md](document_management_plan.md) — see
> "Amendments to the document management plan" at the end, which lists every change to apply there.
>
> ⚠ **Amended by [traceability_plan.md](traceability_plan.md)** on one point: membership and item
> rows (`gws_shared_folder_member`, `gws_shared_folder_item`) must be **auditable entities**, since
> Part 11 requires access-right changes to be audited — `created_by` / `created_at` record current
> state, not history. That plan otherwise **confirms** this one: the `Permission` vocabulary needs no
> change (GxP roles are orthogonal to READ/WRITE/MANAGE), and the "sharing never exceeds `READ`"
> ceiling is favourable to compliance.

## Purpose

Two needs, one mechanism:

1. **Share any object into folders.** A project task, a note, a scenario, a resource, an app must be
   shareable into a folder tree, without moving it and without its owning app knowing about folders.
   Sharing **creates a new access path**: the task stays reachable through its project, and becomes
   reachable through the folder for whoever the folder is shared with.
2. **Unify how rights are expressed** so that a maximum of apps use the same mechanism, instead of
   each one reinventing sharing, revocation and audit.

The second need follows from the first: once sharing is a core capability, apps stop implementing the
*plumbing* of it — table, revocation, audit, search integration.

They do keep two responsibilities, and this document does not hide them: answering two questions about
their own domain (the provider), and **rendering their own UI on a restricted perimeter** when a shared
object is opened. That second one is real work per app — a shared task must open the app's real task
page, with its comments and attachments, not a generic viewer.

---

## What the current code actually looks like

Three findings that shape the design.

### There is no per-object authorization in the platform

`UserGroup` (`user/user_group.py`) is a three-value enum (SYSUSER / ADMIN / USER) compared by rank,
and it has **no consumer outside `user/` itself**. There is no ACL table, no per-object ownership for
rights purposes, no route-level object check. Any lab user sees everything.

This design is therefore **the first per-object access control in the platform**. There is nothing to
retrofit and nothing to stay compatible with — which is an advantage, and the reason the vocabulary
below can be closed rather than negotiated with existing usage.

### `SpaceFolder` is a classification attribute, not a permission

`SpaceFolder` (`folder/space_folder.py`) is a bare `(name, parent)` tree. No `path_cache`, no owner,
no ACL. `ModelWithFolder` adds a nullable FK on Scenario / Note / ResourceModel. **No authorization
code reads it** — the sharing users perceive today happens in the Space, not in the lab; the lab is a
read-only mirror fed by `SpaceFolderService.synchronize_all_folders`.

So "sharing via folders" does not exist lab-side today. This plan does not replace a lab mechanism; it
introduces the first one.

### The event bus already does synchronous cascade-on-delete

`form_note_cascade_listener.py` reacts to `NoteDeletedEvent` to cascade-delete owned forms, with
`is_synchronous() -> True` so it runs **inside the deleting transaction** and rolls the note delete back
on failure. `gws_note` does not know `gws_form` exists; the consumer registers the listener.

This is the exact pattern needed when a shared object's source is deleted (see "When the source
disappears"). It exists, it is proven, and it does not have to be invented.

### The tag system is already keyed the right way

`EntityTag` (`tag/entity_tag.py`) is keyed on `(entity_type, entity_id)` — the same soft-reference
shape used by the document index. It also already carries `is_propagable`, a per-tag flag meaning
"this tag is meant to travel", used today for resource/view propagation. Both facts are reused below
rather than reinvented.

---

## The core decision: a shared folder grants access

The document management plan considered two options and preferred option A (a drive folder holds only
files the drive owns). Its second objection to option B — *"a folder whose contents differ per viewer
is a bad object"* — assumed that **the folder classifies and the app authorizes**, so filing a
document into a shared folder gave nobody access.

**This plan is option C: the folder classifies *and* grants read access.** The objection does not
apply: a shared folder grants access to everything it contains, so it looks the same to every member.
The first objection ("apps have no folder hierarchy to offer") does not apply either, because nothing
is filed automatically — a human deliberately shares a handful of objects; no app is asked to place
its 50 generated resources.

What this introduces, and it must be stated plainly: **an object gains a second access path,
independent of its owning app.** Access becomes `app_access OR shared_access`. That is a real change
in the platform's authorization shape, and everything below exists to keep it safe.

---

## The folder entry is an object of its own

A shared object is not "the source object, seen from elsewhere". It is a **folder entry**: a
first-class object with its own id, its own title and its own tags, which *references* a source entity
and borrows its content.

This is the alias / shortcut model. The content lives at the source; the label is local.

It also solves the use case option A gave up (`document_management_plan.md`, "What is given up"):
grouping three scenario resources, two project documents and one upload into a client deliverable,
each renamed to something the client can read.

| | Source entity | Folder entry |
|---|---|---|
| Identity | its own | its own (`FOLDER_ITEM`, own id) |
| Title | its own | **its own, independent** — set at share time, never synced |
| Tags | its own | its own, **plus** the source's propagable tags, read-only |
| Content | owns it | borrows it, never copies |
| Writes | via the owning app | on the entry only |
| Scope | `project:abc` | `folder_root:xyz` |

**One rule summarises it: the entry owns its metadata, borrows its content, and never writes to the
source.**

### Why the entry needs its own entity id

`EntityTag` is keyed on `(entity_type, entity_id)`. If the entry reused `(PROJECT_TASK, abc-123)` for
its tags, tagging the entry would tag **the task itself** — visible in the project and in every other
share of the same task. "Independently taggable" would be false in practice, and the first tag added
would silently pollute the source.

So the entry is a registered entity type in its own right (`FOLDER_ITEM`), and its tags are
`(FOLDER_ITEM, <entry_id>)`. No new code in the tag layer: the mechanism is already generic.

### Title: the entry is searched on its own title only

The entry's title is independent from the source's, from creation. It is **not** kept in sync, and the
source title is **not** searchable through the entry.

The reasoning: someone searching the original name will find the original object — if they have access
to it. If they do not, they were not supposed to find it. Matching the entry on the source title would
let them reach, through a shared folder, an object they cannot otherwise see, and would leak the
original name.

Consequences: no `source_title` column, no `title_overridden` flag, and no "should renaming the source
propagate?" question — the answer is never.

**UI rule**: the source's real name may be displayed on the entry's detail view **only to users who
have owner access to the source** (they would see it anyway). Hidden from everyone else.

### Tags: read both, write one

Tags are **never copied**. Copying would immediately raise "and if a tag is added afterwards?", "and
if it is removed?", and every answer adds synchronisation that eventually diverges.

- Source tags stay on `(source_type, source_id)`. Nothing touches them.
- Entry tags live on `(FOLDER_ITEM, entry_id)`. They exist only there.
- On read, the entry displays the **union**, with the origin visible: inherited tags (read-only here)
  and local tags (editable).

This answers both questions directly:

- **A tag added to the source after sharing** appears on the entry immediately. No propagation, no
  event, no possible drift — it was never copied, it is a read.
- **A tag added on the entry** stays local. It never travels back to the source, nor to other shares
  of the same source.

The asymmetry is justified by rights: sharing grants **read** on the source. Writing a tag onto the
source would be a write on an object the user may only read. The rule "modify the entry, never the
object" covers tags with no exception.

**Only `is_propagable` tags are inherited.** Two reasons: it reuses an existing, understood flag rather
than inventing a second notion of "travels"; and it closes a leak — a tag can be confidential by its
name alone (`patient:dupont`, `client:acme-buyout`), and inheriting it into a shared folder would
disclose it to people with no access to the source. Requiring an explicit flag makes that a deliberate
act.

**Cost to watch**: tag search must match either set, which is an `OR` across two join conditions.
`EntityWithTagSearchBuilder` already does one join per tag criterion
(`entity_with_tag_search_builder.py:74-91`), so this degrades with several tag filters. Escape hatch if
measurement demands it: a rebuildable projection table of inherited tags — **not** extra rows in
`EntityTag`, which must stay the source's own.

---

## Access model

### One scope per index row (no N-ary scope table)

An earlier draft gave each document a list of scopes (`gws_entity_scope`). Rejected: the search join
would produce duplicates, requiring a `DISTINCT` that a future query can forget — and a forgotten
`DISTINCT` on a security filter is a silent bug.

**A shared entity produces a second index row instead.** Same source, different scope:

```
gws_document_index
├── (FOLDER_ITEM, e-001) src=(PROJECT_TASK, abc) scope=folder_root:xyz  source=SHARED
└── (PROJECT_TASK, abc)  src=NULL                scope=project:abc      source=OWNER
```

`access_scope` stays a scalar `NOT NULL` indexed column. The security join is **unchanged**:

```sql
JOIN gws_user_scope us ON us.scope = di.access_scope AND us.user_id = ?
```

Three properties follow: the filter keeps living inside the index's own search builder and cannot be
forgotten; revocation is a plain `DELETE` of one row, atomic and readable; and nothing in the existing
scope design has to learn a new shape — it just sees more rows.

Since metadata is *deliberately* independent per row (own title, own tags), the duplication objection
against this shape disappears: these are not copies that may drift, they are distinct data.

### Permission vocabulary — closed, three levels

```python
class Permission(Enum):
    READ    # see the object and its content
    WRITE   # modify the content
    MANAGE  # rename, move, delete, share
```

Ordered, and **closed**: an app cannot add values. An app needing "validate a note" or "export a
dataset" keeps that as its own business rule — the core standardises only what is genuinely common.
The pressure to add `COMMENT`, `VALIDATE`, `EXPORT` will come; giving in turns a readable model into a
matrix nobody can reason about. The answer must be "keep it in your app".

### One decision function

```python
AccessService.get_permission(user, entity_type, entity_id) -> Permission | None
```

1. The owning app gives the entity's scope; if the user holds it in `gws_user_scope`, they get what
   the app grants (typically `WRITE` or `MANAGE`).
2. Otherwise, if a folder entry references the object in a folder the user belongs to → `READ`.
3. Otherwise `None` — **fail closed**.

The maximum wins, and **sharing can never exceed `READ`**. That ceiling is what keeps the second access
path safe: it can widen who reads, never who writes, so no app's rules can be circumvented through a
folder.

### A share does not depend on its sharer

**Decision: when the sharer loses access to a source they shared, nothing changes. The entry stays and
keeps granting `READ`.**

The share is an access granted **to the folder**, not a delegation of the sharer's own rights. Once
created it stands on its own: its authority is the folder, whose members are the accountable party. So
there is nothing to cascade when Marie leaves project X — the entries she filed are unaffected.

This is what keeps the model simple, and the simplicity is the point:

- **No revocation graph.** If a share depended on its sharer's rights, every membership change in every
  app would have to walk the shares that user created — a cascade crossing app boundaries, on a path
  where being late is a leak. The whole `gws_user_scope` design assumes scopes are compared, not
  recomputed transitively.
- **No surprise for the recipients.** People who were given access do not lose it because of a personnel
  change in a project they are not part of.
- **`can_share` is checked once, at share time.** It gates the *act* of sharing, not the persistence of
  its result — the same way signing a document does not become void when the signer changes job.

The counterpart, which must be accepted deliberately: **an access can outlive the reason it was
granted.** A task shared by someone who has since left the project remains readable by the folder's
members. That is a governance question, not a correctness one, and the answers are already in the
design — the audit trail says who shared what and when, and folder members can remove an entry at any
time. If it becomes a real problem, an optional expiry date on entries is the fix; noted, not built.

### The list query must be the same decision

The classic failure of this kind of design: a clean per-object function, and list screens that bypass
it because calling it 500 times is too slow. The two paths drift, and the fast one leaks.

**Rule: `get_permission` and the search filter are two expressions of the same join, tested against
each other.** The join is the one above; it does not change shape, because sharing produces an index
row carrying its own scope. This is precisely the property the one-row-per-scope model preserves, and
it is what makes this unification realistic rather than aspirational.

### Provider vs primitive — the sorting criterion

Before listing what apps implement, the criterion that decides *where* each piece belongs. It matters
because getting it wrong produces interfaces nobody can call:

> **A provider is justified only if generic core code calls it while iterating the registry, knowing no
> app. Otherwise it is a primitive the core offers and the app calls.**

Both exist in this design, and confusing them is what produced a rejected draft (see below).

| | Direction | Example |
|---|---|---|
| **Provider** | core → app, core loops over the registry | `get_owner_scopes`, `can_share` |
| **Primitive** | app → core, the app calls where it knows it matters | `auth.check_within_shared_scope(...)` |

### What apps implement — two methods

```python
@entity_access_provider(entity_type="PROJECT_TASK")
class ProjectTaskAccess(EntityAccessProvider):

    def get_owner_scopes(self, user) -> list[str]:
        """This user's owner perimeters. Called by the core to build gws_user_scope
        (login, rebuild, reconciliation) — it iterates every registered app."""
        return [f"project:{p.id}" for p in ProjectMember.projects_of(user)]

    def can_share(self, entity_id, user) -> bool:
        """Who may expose this object outside the project.
        Called by the core sharing service before creating a folder entry."""
        return ProjectMember.has_role(user, task.project_id, ["OWNER", "EDITOR"])
```

Both pass the criterion: the search joins `gws_user_scope` without knowing who filled it, and the drive
calls `can_share` without knowing what a project is.

**`get_entity_scope` is deliberately *not* a third method.** An entity's own perimeter is already
declared through `IndexedDocumentModel.get_document_descriptor()`
([document_management_plan.md](document_management_plan.md), "Providers, and a mixin for the common
case") — the mixin is already the generic call site, so a provider method would be a second way to
declare the same fact, and the two would drift. That is precisely the failure the document plan
documents for its five parallel entity enums. The scope belongs in the descriptor; the `DocumentProvider`
already defined there covers the two cases the mixin cannot (entities that cannot inherit it, such as
`ResourceModel`, and rebuild-time re-enumeration where no instance is in hand).

`can_share` is not optional: without it, anyone able to read a confidential task could republish it to
the whole lab. **Default rule: only a user with *owner* access (not merely shared access) may share**,
otherwise a share re-shares in cascade and control is lost. An app that does not register a provider is
simply not shareable; nothing breaks.

### This is what makes it easier on the project side

Today, for `gws_project` to allow sharing a task outside the project, it would have to build a shares
table, a UI, revocation, audit and search integration — and `gws_note` would build the same again.

With this mechanism `gws_project` implements **none** of it. It answers two questions about its own
domain; the core does the rest. After sharing, `gws_project` has nothing extra to manage: the task
stays its task, with its rules; the external access lives in parallel in a table it does not know, and
disappears when the entry is removed.

What it *does* take on is the restricted-entry UI — see the next section.

---

## Opening a shared object: the app's own UI, on a restricted perimeter

**Decision: a shared object opens in its owning app, in that app's real UI — not in a generic viewer.**

A generic read-only card was considered and rejected. For a project task the comments, attachments and
subtasks *are* the content; a generic card would render a degraded copy of a screen the app already
has, and would push every app to write a second, worse version of its own UI.

So the constraint is not "never enter the app" (an earlier draft of this document said that, and it was
too broad — it made sharing useless). It is **"enter the app on a restricted perimeter"**.

The platform already does this one level up: the app token carries `typ:"app"` + `app_id`, opens the
~20 `_or_app` routes and is rejected by the other 344 (`apps/APP_LAUNCH_AND_AUTH.md`). A space visitor
enters an app without ever obtaining a lab session. **Object sharing is the same pattern, one notch
finer: a credential naming an app *and* an object.**

```
gws_code (single use)  →  token {typ:"shared", app_id, entity_type, entity_id, perm:READ}
```

The app boots on its own route — the real task page, with its tabs, comments and attachments. It does
not switch to a degraded mode. What changes is the perimeter the lab answers within.

### How the perimeter is enforced — a primitive, not a provider

A rejected draft gave the provider a `get_shared_closure(entity_id)` returning the sub-entities a share
also grants (comments, attachments, subtasks). **It has no possible caller**, and that is why it is
recorded here rather than silently dropped:

- To authorise a request on comment `c-42`, the core would have to go *from the sub-object to the
  shared object* — the inverse of what the closure returns. Answering would mean expanding the closure
  of every object shared with the user on every request.
- Freezing the closure at share time fixes the direction but breaks the semantics: a comment added
  after sharing would be invisible — the same "never copy, always read" rule that governs tags.

**The workable direction is the reverse question.** The core does not ask "is this comment shared?". It
carries the shared perimeter in the auth context, and the app — which alone knows that a comment
belongs to a task — checks membership:

```python
# in gws_project's comment service
def get_comment(comment_id, auth: AuthContext):
    comment = TaskComment.get_by_id_and_check(comment_id)
    auth.check_within_shared_scope("TASK", comment.task_id)   # no-op on owner access
    return comment
```

`check_within_shared_scope` is a **core primitive**: no-op when the context is an owner access; requires
equality when the context is a share; raises otherwise. One comparison — no graph walk, no enumeration.
`AuthContext` already has `AuthContextApp` and `AuthContextShareLink` variants
(`user/auth_context.py`); this adds a third.

### The honest cost: the guarantee moves into the apps

With central filtering, forgetting a filter was impossible. Here, a `gws_project` route that forgets
`check_within_shared_scope` leaks. That is a real regression in safety and is stated rather than
dressed up. Three things keep it acceptable:

- **Fail closed, opt-in per route.** A route is not reachable with a shared context unless explicitly
  marked so. Forgetting the *call* on an unmarked route does not open it; the route simply refuses.
  This is the property that bounds the damage of an oversight.
- **Same model as the app token**, which is already an explicit list of ~20 routes against 344 refusing
  ones. One notch finer, not a new principle.
- **Testable** — "this shared context reaches exactly these routes, with exactly these ids" must exist
  as a test suite before the first provider ships.

### ⚠ Unresolved: list queries

Fetching one comment by id checks cleanly. Fetching "the comments of task abc" checks cleanly too. But
"the tasks of project X", called by the same screen to populate a menu, must return a single row — and
that is *filtering*, not verification. Each app must handle its list endpoints one by one.

**This is the real implementation cost of sharing, per app**, and it is higher than the two provider
methods suggest. It should be measured on `gws_project` before committing other apps.

### Sharing an app

Same mechanism with a credential naming the app and no object. Two consequences:

- **`READ` on an app means the right to launch it.** No fourth permission value: the vocabulary stays
  closed and the verb is documented for this entity type. Adding `EXECUTE` would open exactly the door
  this plan keeps shut, and the next request would be `VALIDATE`.
- ⚠ **Sharing an app shares what the app can reach**, not just the app. The `_or_app` routes must filter
  by the user's scopes, otherwise a widely shared app becomes a way around per-object rights. This is a
  condition of app sharing, not an enhancement.

### Left to each app: what surrounds the object

The app opens on the task, but breadcrumbs, project name and member avatars usually live in the page
chrome. The lab can refuse the underlying calls (403), but each app must decide what to display
instead. This is per-app work and should be known before promising sharing across five apps.

---

## Schema

```sql
gws_shared_folder(
    id, name, parent_id, root_id, is_root,
    created_by, last_modified_by, created_at, last_modified_at
)

-- sharing is at root level only (see below). Individual users in V1: no named groups exist.
gws_shared_folder_member(root_id, user_id, role, created_by, created_at)   -- UNIQUE(root_id, user_id)

-- SOURCE OF TRUTH for sharing. The index rows are its projection.
gws_shared_folder_item(
    id,                                  -- becomes the FOLDER_ITEM entity_id
    folder_id,
    source_type, source_id,              -- soft reference, NO FK
    title,                               -- the entry's own title, independent from the source
    shared_by, shared_at,
    UNIQUE(folder_id, source_type, source_id)
)

gws_shared_folder_item_audit(item_id, action, user_id, at)   -- added / removed
```

Changes to `gws_document_index` (see amendments):

```sql
    entity_type, entity_id,              -- identity of THIS row (FOLDER_ITEM for a share)
    source_type NULL, source_id NULL,    -- referenced entity; NULL on an OWNER row
    scope_source,                        -- 'OWNER' | 'SHARED'
    folder_id NULL,                      -- the folder, for SHARED rows (and drive-owned rows)
    UNIQUE (source_type, source_id, access_scope)
```

`scope_source` is required for three concrete reasons, not for tidiness:

- **Display dedup** — a user who is both a project member and a folder member sees the task twice.
  Group by source at presentation time and prefer the `OWNER` row, which also yields the right UI
  message ("you have access via the project", not "via Marie's folder").
- **Reindexing** — reconciliation walks entities, not rows. Without the marker it would treat `SHARED`
  rows as orphans and delete them, i.e. **revoke accesses on its own**.
- **`folder_id` meaning** — the document plan says it is meaningful only for `owner_app = "DRIVE"`;
  it now applies to every `SHARED` row.

### Root-level sharing only

Only a root folder is shareable; sub-folders inherit and cannot be shared individually. The scope stays
a flat string compared by equality (`folder_root:<root_id>`), so the join, the index query and RAG chunk
metadata are unchanged. Full inheritance would make a document's scope depend on its whole parent chain,
so moving a folder near the top would invalidate every descendant's scope — thousands of index rows plus
RAG metadata propagation.

Moving a sub-tree between roots therefore changes the scope of every entry beneath it: rare, explicit,
must be transactional, and must emit "perimeter changed".

**The UI must state that sharing lives at root level**, not merely disable the button elsewhere.

---

## Operational rules

These are conditions, not refinements — this is the first authorization mechanism in the platform and
it sits on the path of every search.

- **Removal is synchronous and transactional, never queued.** Granting late is benign; revoking late is
  a leak. Same asymmetry as `gws_user_scope`.
- **`gws_shared_folder_item` is the source of truth; index `SHARED` rows are its projection.** See the
  warning below.
- **Audit** — who shared what, when, and who removed it. It will be asked for.
- **Fail closed** — an app whose provider is unavailable drops *its* results; never open by default,
  never break the whole search.
- **Deleted sources are pushed, not polled** — see the section below. Reconciliation stays as the
  safety net, not the mechanism.

### When the source disappears — the app pushes the event

**Decision: the owning app emits a deletion event (or calls the API); the drive and the document index
react. No polling, no scan.**

There is a precedent to copy exactly: `form_note_cascade_listener.py` cascades form deletion on
`NoteDeletedEvent`, **synchronously, inside the deleting transaction** (`is_synchronous() -> True`), so
a failure rolls the whole delete back. The listener is registered by the consuming side, and `gws_note`
knows nothing about forms. Same shape here — `gws_project` emits, the core reacts, and the golden rule
is intact in both directions.

```
gws_project deletes a task
      → emits EntityDeletedEvent(entity_type="PROJECT_TASK", entity_id=...)
          → core listener: delete the OWNER index row
                           resolve gws_shared_folder_item by (source_type, source_id)
                           delete the SHARED index rows
                           delete the entries + their tags (audit row kept)
                           emit "perimeter changed" for the RAG
```

This is the one case where the **event** is right and the direct call of the document plan is not: the
deleting app must not know that folders, an index or a RAG exist. Exactly the criterion that plan sets
out ("events are the right tool when the emitter must not know anyone is listening") — indexing fails it,
deletion passes it.

Two rules, matching the existing listener:

- **Synchronous, inside the delete transaction.** Removing access is the same asymmetry as revocation:
  never queued. If the cascade fails, the source delete rolls back rather than leaving entries pointing
  at a deleted object.
- **Idempotent.** A replay, a reconciliation pass and the event itself must converge on the same state.

**Reconciliation remains** — for hard deletes that bypass the model, crashes between transactions, and
apps that have not yet emitted. It is the net, not the mechanism; a dangling entry is a bug to be
caught, not the normal path.

#### What happens to the entry itself (settles open point 3)

**Decision: the entry is deleted, along with its index rows and its tags.** The cascade is complete —
nothing survives the source.

The entry is a *pointer with a label*, not a document. Once the source is gone it designates nothing:
its title describes an object that no longer exists, its tags qualify content nobody can open, and
opening it can only produce an error. Keeping it would preserve the packaging of something that is no
longer there.

A tombstone state (kept, marked unavailable, not openable) was considered and rejected:

- It keeps a **row that must grant nothing** in a table whose whole purpose is to grant. Every query —
  search, folder listing, scope join, RAG — then needs the "except tombstones" case, and the one that
  forgets it is a leak on a dead reference. A design whose safety depends on remembering an exception
  everywhere is worse than one with no exception.
- It **accumulates**. Nobody cleans up an entry that does nothing, so shared folders slowly fill with
  dead labels, and the folder stops being trustworthy.
- The information it was meant to preserve is better served by the **audit trail**
  (`gws_shared_folder_item_audit`), which already records what was shared and when. History belongs in
  a history table, not as a disabled row in a live one.

**What the recipient sees**: the entry disappears from the folder. This is the same behaviour as any
shared reference whose target is deleted, and the audit trail answers "what was here?" for anyone who
asks. If usage shows people are genuinely disoriented, a notification to folder members is the fix —
not a persistent dead row.

Consequence for the schema: **no `source_deleted` column**. Deletion is deletion.

### ⚠ The index is no longer fully rebuildable from apps

`document_management_plan.md` states that the index is "a projection, never a source of truth, fully
rebuildable" by asking every provider to re-enumerate. **That is no longer true for `SHARED` rows**: no
app `enumerate()` can produce them, because no app knows about sharing.

A rebuild that only replays providers would **erase every share in the lab**. The rebuild procedure must
re-project `gws_shared_folder_item` as well. This is the most dangerous consequence of the design and it
must be explicit in both documents.

---

## RAG integration

A folder entry has its own id and its own scope, so its chunks are indexed under
`(FOLDER_ITEM, <id>)` with the folder scope — chunk metadata stays a scalar scope, as the document plan
assumes. Sharing and unsharing emit the plan's existing "perimeter changed" trigger (metadata-only
update, no embedding call).

Embeddings would be duplicated if a shared entity were naively re-indexed. Since `content_hash` is
identical, chunks can be reused with only metadata varying. Not resolved here; noted for the RAG step.

The plan's SQL verification of retrieved ids becomes **more** necessary, not less: it is what catches
any desynchronisation between shares and chunk metadata.

---

## Points to settle

1. **Named groups.** Everything here works with individual members but does not scale without groups.
   `UserGroup` is a three-value enum with no consumer outside `user/` — there is nothing to share
   *with* yet. This is the structural prerequisite for anything beyond tens of folders.
2. **Sharing requires indexing.** A share is an index row, so an entity must be indexable to be
   shareable. The document plan defers "which resources are indexed" to the `gws_workflow` refactor;
   that decision is no longer only about search noise — **it gates what can be shared**, so it moves up
   in priority.
3. **Inherited-tag search cost** — the `OR` across two join conditions, and whether the projection table
   is needed. Unmeasured.
4. **Can an entry be shared into a second folder?** `UNIQUE(folder_id, source_type, source_id)` allows
   the same source in several folders (two entries, two scopes, two titles). Coherent, but the UI must
   make it legible.
5. **Permission vocabulary pressure.** Documented as closed; the first app to ask for a fourth level is
   the test of whether this holds.
6. **List endpoints under a shared context** (see "Unresolved: list queries"). Verification per object
   is solved; filtering per collection is per-app work of unknown size. **Measure it on `gws_project`
   before committing other apps** — this is the item most likely to change the cost estimate.
7. **Scope-filtering the `_or_app` routes.** A prerequisite of app sharing, not of object sharing, but
   it lands in the same release if apps are shared through the drive.
8. **Page chrome under a restricted perimeter** — what each app shows in place of breadcrumbs, project
   name and member lists. Per-app product decision, not a core one.

---

## Sequencing

Steps 1–3 deliver a usable sharing feature without waiting for the full document index.

1. **Entity-type registry** (prerequisite, shared with the document plan) — `FOLDER_ITEM` must be a
   registered type for tags to work.
2. **Contract** — `EntityAccessProvider` (two methods), `Permission`, `AccessService.get_permission`,
   the `AuthContext` shared variant and `check_within_shared_scope`, the registry. Pure code, no DB.
3. **Folders + entries** — `gws_shared_folder*` tables, share/unshare, root membership, audit. One real
   provider (`gws_project.Task`) to validate the contract on real data, **including its restricted-entry
   UI and its list endpoints** — the step that measures the per-app cost before other apps commit.
4. **Index projection** — `SHARED` rows, `scope_source`, `source_*`, the amended `UNIQUE`, and the
   rebuild procedure that re-projects shares.
   Plus **`EntityDeletedEvent` + the synchronous core listener** (full cascade: index rows, entries,
   entry tags; audit kept; RAG perimeter event), modelled on `form_note_cascade_listener.py`.
5. **Search integration** — one filter for both paths, dedup by source, inherited tags.
6. **Other providers** — Note, ResourceModel, Scenario.
7. **RAG** — perimeter events for share/unshare, chunk reuse by `content_hash`.

---

## Amendments to the document management plan

To apply in [document_management_plan.md](document_management_plan.md):

1. **Point 1 of "Points to settle" (option A vs B) becomes A vs B vs C.** Objection 2 to option B does
   not apply to C — a granting folder has the same contents for all its members — and objection 1 does
   not either, since nothing is filed automatically. Without this, a reviewer rejects C by assimilation
   to B.
2. **`UNIQUE (entity_type, entity_id)` → `UNIQUE (source_type, source_id, access_scope)`** (lines 420
   and 462).
3. **Add `source_type`, `source_id`, `scope_source`** to the schema; `entity_type/entity_id` now
   identify the row, not the referenced entity.
4. **`folder_id`** is no longer meaningful only for `owner_app = "DRIVE"` — it applies to every `SHARED`
   row.
5. **`IndexedDocumentModel`'s upsert must target the `OWNER` row only**, otherwise saving a note
   overwrites or duplicates its share rows.
6. **Amend the rebuildability claim** (lines 83, 92-94): `SHARED` rows are projections of
   `gws_shared_folder_item`, not of any app provider.
7. **The abandoned "mixed-origin deliverable" use case** ("What is given up") is now covered by folder
   entries with independent titles.
8. **"Which resources are indexed" is promoted** from a deferred `gws_workflow` decision to a
   prerequisite of sharing.

## Amendments to the split plan

To apply in [modular_apps_split_plan.md](modular_apps_split_plan.md):

- Add this document to "Companion documents".
- **Point 17** (`share/`, `space/` — core modules referencing domain entities) gains a concrete answer
  for the sharing half: `EntityAccessProvider` is the registry treatment it calls for. `ShareLink`
  (outbound, public links) stays a separate concern from internal sharing and should not be merged
  into it.

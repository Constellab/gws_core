# Traceability — audit trail, compliance mode & electronic signature

> Design document, part of the modular refactor. It builds on
> [modular_apps_split_plan.md](modular_apps_split_plan.md) (entity-type registry, soft references,
> event bus) and on [shared_folders_plan.md](shared_folders_plan.md) (the `Permission` model, which
> this plan does **not** change but does extend with an auditing obligation) — see
> "Amendments to the other plans" at the end, which lists every change to apply elsewhere.

## Purpose

Give app developers the tools to build applications that can pass a pharmaceutical audit — GxP,
21 CFR Part 11 / EU Annex 11, ALCOA+ data integrity. The target is the **strictest** level (GxP),
not a lowest common denominator.

Concretely, three things the platform cannot do today:

- an **audit trail** that records who changed what, from which value to which value, when and why —
  and that can be shown to be complete and unaltered;
- a **compliance mode** that hardens the rules (no hard delete, mandatory signature, mandatory
  reason) on the subset of data that needs it, without imposing that cost on the whole lab;
- an **electronic signature** with meaning ("reviewed by", "approved by"), bound to the signed
  content in a way that cannot be silently detached.

### Scope boundary — stated deliberately

This plan makes an application **auditable**. That is necessary but *not sufficient* for a customer
to be compliant. Explicitly **out of scope**: software validation (GAMP 5 — IQ/OQ/PQ, requirement
traceability matrices), SOP management, user training records, and qualified third-party
timestamping. Those stay with the customer. A document that says what it does not do is more
credible in review than one that promises "compliance".

---

## What the current code actually looks like

### `Activity` cannot become an audit trail as-is

`Activity` (`user/activity/activity.py`, table `gws_user_activity`) records `user`,
`activity_type`, `object_type`, `object_id`. It has **four disqualifying properties**, each of
which an auditor would find on their own:

1. **Events are deliberately merged and overwritten.** `add_or_update()` looks for a same-type
   event within a 5-minute window (`ACTIVITY_MERGE_MAX_TIME`, `activity.py:25`) and, if found,
   **mutates that row's `last_modified_at` instead of inserting** (`activity.py:64-68`). Events are
   lost by design, and the table is updated in place.
2. **Writes are fire-and-forget, in a separate thread.** `ActivityService.add_or_update_async()`
   starts a bare `Thread` and never joins it (`activity_service.py:62-76`). This is the form used by
   nearly every call site (`note_service.py`, `scenario_service.py`). A write can fail silently, and
   it is not ordered with respect to the mutation it describes.
3. **Failures are swallowed.** `add_with_catch()` turns any exception into a log line and returns
   `None` (`activity_service.py:38-44`).
4. **No before/after values, no reason, no correlation** between the rows produced by a single user
   action.

Plus a modelling limit: `ActivityObjectType` is a closed 7-value enum (`activity_dto.py:22-30`)
containing `PROCESS` and `USER` but **not `RESOURCE` and not `VIEW`** — it cannot describe most of
what the lab produces.

**Decision: `Activity` is rethought from scratch as a real audit trail.** The UI activity feed and
the audit trail have contradictory requirements (the feed wants compact and readable — hence the
merging; the audit wants exhaustive and immutable), so they are two tables, the feed being
derivable from the trail.

### What already exists and is worth building on

- **Validation as a freeze.** `Scenario.validate()` (`scenario.py:243-263`) sets
  `is_validated` / `validated_at` / `validated_by`, and `is_validated` then blocks updates
  (`scenario.py:409-410`). This is a working approval primitive and the natural seed for the
  signature model.
- **Reproducibility is real.** `brick_version_on_run` and `brick_version_on_create` are recorded
  per process (`process_model.py:80`, `process_run_stat_model.py:28-29`), so a run can be replayed
  with the same task code. This is the platform's strongest asset in front of an auditor — see the
  two gaps in point 6.
- **Impact is computed before acting.** `_calculate_scenario_reset_impact()`
  (`entity_navigator_service.py:84-94`) enumerates affected entities before a destructive action,
  and the front already calls it (`check_impact_for_scenario_reset`). In compliance mode this
  becomes the thing the user must explicitly confirm, and the confirmation is what gets recorded.
- **No per-object permissions yet.** As `shared_folders_plan.md` notes, its `EntityAccessProvider` /
  `Permission` model is the platform's *first* per-object access control. Part 11 requires access to
  be limited to authorised individuals, so that plan is a **prerequisite** of compliance mode, not a
  parallel concern.

### Audit leaks in the current write paths

Three families of writes bypass instance hooks. Each is a hole an audit trail cannot tolerate,
and they must be closed before compliance mode can be claimed:

1. **`Model.save(skip_hook=True)`** — the parameter exists (`model.py:139`) and short-circuits
   `_before_update()`. It is a documented escape hatch out of auditing.
2. **Bulk `delete().where(...).execute()`** — no instance hook runs. Present on business entities,
   not just technical ones: `note.py:151`, `note.py:181`, `note_form_model.py:65,70`,
   `scenario.py:288`, `task_input_model.py:87`, `queue.py:92`, `triggered_job_model.py:158`.
3. **Migrations** — raw SQL by design. Treated as a system-level audit event ("migration X applied"),
   not row by row.

---

## Architecture

### Layer 1 — Compliance mode governs policy, not capture

The tension in an *opt-in* compliance mode is that an audit trail a developer can forget to wire up
has no value: "what guarantees every change is recorded?" cannot be answered with "the developer
remembered". The resolution:

- **Capture is structural and always on.** It lives in the core `Model` write path, for every entity
  type declared auditable. A developer cannot write to the database without going through it. One
  code path, always tested.
- **Compliance mode governs the rules**: no hard delete, mandatory reason, mandatory signature on
  declared transitions, re-authentication, retention, refusal to purge.

The decisive benefit: when compliance mode is switched on for existing data, **the prior history is
already there**. With optional capture, enabling the mode creates a gap in the trail at exactly the
date the auditor cares about.

**Granularity: per root entity** (a project, a folder), inherited by child entities — not per app.
A single `gws_project` deployment typically hosts both GxP and exploratory projects. Switching a
root *into* compliance mode is **irreversible**; otherwise the mode proves nothing.

### Layer 2 — Two levels of record in one table

A `Model`-level hook captures **row mutations**, not **business intent**. "The user approved the
dossier" becomes three updates across three tables. An audit trail must read as a story, not as a
replication log. So one table, two natures of row, correlated by a unit-of-work id:

| | intent row | field rows |
|---|---|---|
| `action_id` | its own id | the parent's `action_id` |
| `intent` | `SCENARIO_RESET` | empty |
| entity | the targeted entity | each mutated object |
| diff | aggregated summary | per-field before/after |
| written by | the service, explicitly | the hook, automatically |
| reason | user-supplied, when required | — |

The automatic level guarantees nothing is missed; the explicit level guarantees it is intelligible.
Only the automatic level is illegible; only the explicit level reintroduces the forgetting problem.

The auditor reads intent rows and unfolds to field rows on demand. The intent row carries an
aggregate summary ("1 scenario reset, 12 processes cleared, 1 note deleted"), computed when the unit
closes, so the log is browsable without unfolding.

### Layer 3 — Where the trail lives

**One table in the core**, keyed by a soft `(entity_type, entity_id)` reference, no FK — the
`EntityLink` pattern. Reasons:

- an auditor asks "the complete history of this object" or "everything this user did in March";
  a table per app turns that into an N-source aggregation, some of which may be uninstalled;
- the audit trail is **the one object in the system that must survive an app being uninstalled**.
  The document index is deleted on deactivation because it is rebuildable; the audit trail is not
  rebuildable and must be kept, with `entity_type` values that become orphaned. This asymmetry is
  deliberate.

Consequence to accept: this argues for **option A of point 12** (single database) in the split plan,
or at minimum requires the core DB to be writable from every module.

Auditability is a **capability of the entity-type registry** (`auditable`, alongside `taggable` /
`navigable` / `indexable`), which also carries the **serialisation contract**: which fields to
audit, which to exclude (blobs, caches), and how to summarise non-diffable fields (rich text, large
JSON) — typically by hash rather than by value, or the trail grows larger than the database. This
replaces the closed `ActivityObjectType` enum, consistent with points 1+2 of the split plan.

---

## Capture mechanism

### The hook

`Model.save()` already distinguishes insert from update via `force_insert` and exposes
`_before_insert()` / `_before_update()` (`model.py:118-156`). Peewee natively tracks changed fields
in `self._dirty` — unused anywhere in gws_core today, but reliable. On update:

```
dirty = self._dirty                            # fields actually modified
old   = type(self).get_by_id(self.id)          # state in database
diff  = {f: (getattr(old, f), getattr(self, f)) for f in dirty}
```

**Cost: one extra SELECT per update.** That is the real price of per-field before/after, and it is
accepted knowingly. Two mitigations: only for entity types declared auditable (so never for
`ProgressBar`, `Monitor`, `Job`, `Typing` — high-throughput technical tables), and snapshot at load
time instead of re-reading when the object was just fetched.

On **delete** of an auditable entity, store a **full snapshot**, not a diff — the only case where
complete state is recorded. Otherwise the trail references ids of objects that exist nowhere else,
which proves nothing.

### Closing the leaks

Making the bypass **impossible, not discouraged** is the only version that survives an audit. On an
auditable entity in compliance mode, `delete()` / `update()` at the `Model` level raise, forcing
callers through an auditing path. This is a one-off inventory job (~8 existing call sites listed
above); an architecture test then prevents new ones. `skip_hook=True` is likewise rejected on
auditable entities.

### The ambient context

An action context is propagated implicitly, modelled on the existing `CurrentUserService`:

```
with AuditContext.action(
        intent="SCENARIO_RESET",
        target=(SCENARIO, scenario_id),
        reason=payload.reason):     # required if the entity is already signed
    EntityNavigatorService.reset_scenario(id)
```

Everything written inside the block carries the same `action_id`. The hook knows nothing about
intent — it reads the ambient context.

**Where the context is declared — three layers, each declaring what only it knows:**

1. **A middleware** (not each route) opens a request context: caller, authentication mode,
   timestamp, origin. Automatic, no route to modify, and future routes are covered with no risk of
   omission. Equivalents are needed for the queue, triggered jobs, proxies and apps.
2. **The service declares the intent.** Not the controller — the same services are reached from
   `queue_service`, `triggered_job_service`, `datahub_s3_server_service`, `external_lab_service`,
   `scenario_transfert_service`, `scenario_proxy` / `process_proxy` (tasks and tests) and
   `space_controller` (a different authentication). Controllers are one-line delegations
   (`scenario_controller.py:214-218`); a route-level context would miss every non-HTTP caller — and
   would miss Reflex apps entirely, which have no `core_app` route at all, though they are the
   target. Declaring at service level also means the intent is correct whichever caller invokes it,
   it lives with the transaction (`@GwsCoreDbManager.transaction()` is already on the service,
   `entity_navigator_service.py:44`), and nested contexts express composition: `delete_scenario`
   calls `reset_scenario` (`entity_navigator_service.py:57`), yielding a deletion with the reset as
   a sub-action.
3. **The route passes the reason** as a parameter. It is data, not context.

The deciding test: *if I call this service from a test or from a task, is the trail correct?* At
service level, yes.

Side benefit: instrumenting at service level yields an explicit inventory of the product's auditable
business operations — exactly what a compliance review asks for, and being code, it cannot silently
become false.

### Transaction alignment — and its trap

Aligning the unit of work with the DB transaction means a rollback also discards the trail: we do
not audit what did not happen. But the inverse trap matters for compliance: **a rejected attempt
would leave no trace**, and "user X attempted an unauthorised action" is precisely what an auditor
wants to see. Hence two categories:

- **successful mutations** → inside the transaction, rolled back with it;
- **rejected attempts** (permission denied, entity locked, invalid signature) → written **outside
  the transaction**, in autocommit, so they survive the rollback.

### Writes outside any action context

A background job, an event listener or a CLI script writing with no context produces orphan field
rows. Recommended: **tolerant by default** (implicit `SYSTEM` intent), **strict in compliance mode**
(writing to an auditable entity outside an action context raises). Failure is then loud at
development time rather than silent at audit time, and instrumentation becomes progressive and
verifiable instead of one large up-front project.

---

## Tamper evidence — hash chaining

### Chain shape: per unit of work, globally chained

Three candidates were considered:

- **per row, globally** — cryptographically strongest, but requires total serialisation of inserts:
  a lock held for every write. With a hook producing hundreds of rows for one reset, unworkable.
- **per entity** — does not give the guarantee that matters: deleting *all* rows of an entity leaves
  a perfectly valid chain, and that is the most likely attack.
- **per unit of work, globally chained** — chosen.

```
child_hash(1) = H( unit_id || canonical(child_1) )
child_hash(k) = H( child_hash(k-1) || canonical(child_k) )      for k > 1
children_root(n) = child_hash(last)          # or a Merkle root

unit_hash(n) = H( unit_hash(n-1) || children_root(n) || canonical(intent_n) )
```

Field rows are chained **in memory**, inside the transaction, with no lock and no database read.
Only the intent row takes a link in the global chain — so the serialising lock is acquired **once
per user action**, not once per row. A scenario reset with hundreds of mutations consumes one link.
And the property that matters is kept: deleting an entity's rows breaks the global chain, because
the intent row covering them is gone.

Design details that are not conventions but decisions:

- **`canonical(intent_n)` is included** in the global link. Without it, the author or the reason of
  an action could be changed without breaking the chain.
- **Children are anchored on `unit_id`**, not on `unit_hash(n-1)`. Anchoring on the previous global
  link would require knowing it at unit *open* time, holding the serialising lock for the whole
  action. The `unit_id` (a UUID generated at open time, itself sealed by the global chain via the
  intent row) gives the same anti-replay protection at zero concurrency cost. Without any anchor,
  two units producing identical mutations produce identical child chains, so a block of children
  could be transplanted from one unit to another undetected — realistic, since two successive resets
  of the same scenario produce identical diffs.
- **A unit with no children** (an audited read, a rejected attempt) uses an explicit conventional
  value for `children_root` — never an empty string treated as "absent", which would make
  verification ambiguous.
- **Genesis** `unit_hash(0)` is a fixed constant including a lab identifier, so an audit block cannot
  be transplanted between labs.
- **An integer sequence column** is required: `Model`'s UUID `id` (`model.py:36`) gives no ordering
  and `created_at` is neither precise nor unique enough. This is a deliberate departure from the
  `Model` convention.
- **Canonical serialisation must be deterministic and versioned**: fixed key order, single date
  format, stable representation of `None` and decimals, explicit encoding. If it depends on Python
  `dict` ordering or on locale, the chain becomes unverifiable after a version bump and the trail
  declares itself corrupt. This is the most common failure mode of such mechanisms.

### Concurrency

Two transactions may read the same `unit_hash(n-1)` and both commit, forking the chain; a rollback
after consuming a link leaves a gap. Two options:

- **Serialising lock** on computing the link (`SELECT ... FOR UPDATE` on a dedicated pointer row, or
  a MariaDB named lock) — recommended. An audited user action is not a high-throughput path (tens
  per minute, not thousands per second), and "always sealed" is far easier to defend than "sealed
  within 5 minutes".
- **Seal afterwards**, over the sequence order, by a periodic sealer — decouples performance, at the
  cost of a window where recent rows are unsealed.

Revisit if compliance mode is applied to workloads generating many automatic actions.

### Anchoring: it is the **end** of the chain that must be externalised

A common error to avoid: the genesis hash is a public constant. Knowing it helps no attacker, and
not knowing it prevents no one from recomputing the chain — a DBA editing row 50 restarts from
`unit_hash(49)`, which is in the table in front of them. **Externalising the genesis achieves
nothing.**

What stops them is that `unit_hash(N)` changes. So the **current chain end** is anchored
periodically (every N links or every X minutes) to a store outside the DBA's reach: each anchor
freezes everything before it, and falsification is only possible within the window since the last
anchor. This also closes the truncation gap (deleting the last N rows otherwise leaves a valid
chain).

An anchor is minimal — sequence number, hash, timestamp — so destinations are open: the Space (a
channel already exists), an append-only file outside the database, an external log service, a
qualified timestamping service if a customer requires it. Only one property matters: **the account
writing anchors must not be able to rewrite them**, and the database administrator must not have
access. Otherwise the problem has moved, not been solved.

### Use a plain hash, not a HMAC

Verification must require **no secret**: the auditor reads the rows, recomputes, compares to the
anchors. With a keyed mechanism, the verifier would need the key, and holding it would allow
forging. A plain hash is *stronger* here precisely because it needs no secret to verify. This is
counter-intuitive enough that it is written down so nobody later "improves" it by adding a key.

### Trust model — the honest version

| Who | Can modify a row? | Can rewrite the chain? | Detected? |
|---|---|---|---|
| User via the app | no (insert-only) | no | — |
| Application admin | no | no | — |
| DBA / direct SQL | yes | yes, back to the last anchor | **yes**, by the anchors |
| DBA **+** control of anchors | yes | yes | no |

The last row is the system's limit and must be stated: the guarantee rests on a **separation of
duties** between whoever administers the database and whoever holds the anchors. This is what an
auditor expects to hear — separation of duties is a concept they know better than cryptography.

Two cheap complementary measures, both persuasive in review: an application DB account with **no
`UPDATE` / `DELETE`** on the audit table (prevention, not detection), and the chain verifier exposed
as a **CLI command** so the demonstration takes thirty seconds.

### Corrections are amendments, never rewrites

Recomputing the chain to change a value is never a legitimate operation. A wrong value is corrected
by **appending** a correction row referencing the one it corrects; both remain visible. This is a
GxP rule in its own right: records are amended, not modified.

---

## Reproducibility & data integrity (ALCOA+)

Task code is already versioned per run (`brick_version_on_run`). Two gaps remain before it holds up:

- **Environment versions.** Task code is pinned, but if a conda/mamba/R environment resolves a
  dependency differently at replay, results change. A lockfile (or its hash) must be frozen at run
  time.
- **Checksums.** There are none today — the split plan notes "no checksum on `FSNodeModel` /
  `ResourceModel`". A single `content_hash` column serves three needs at once: dedup (split plan
  point 7), ALCOA+ integrity, and the tamper-proof content↔signature binding (below). **Best
  value-to-effort item in this plan, and independent of everything else — implementable now.**

Also note split plan point 14: persisted typing names embed the brick name and will change in the
split. Replayability of validated scenarios depends on the alias mechanism planned there.

---

## Retention and deletion

In compliance mode, hard delete is replaced by soft delete plus retention. The existing guardrail
is a good starting point: `check_is_updatable()` is already called before destructive navigation
actions (`entity_navigator_service.py:92`) and `is_validated` already blocks updates
(`scenario.py:409`) — it must be extended to soft delete rather than reinvented.

**Purging bytes while keeping the descriptor and hash** is acceptable for *reproducible
intermediates* ("this file existed, here is its fingerprint, it is reproducible by re-execution"),
and not acceptable for *source data*, which can never be reproduced. Optional for V1.

This requires a usable **source / intermediate / result** distinction. `ResourceOrigin` does not
provide it cleanly today — the document plan already found it mixes two dimensions and settled an
`origin_type` vocabulary (`UPLOADED | AUTHORED | GENERATED | IMPORTED | DERIVED`). Whether that is
sufficient to drive purge policy is **to be confirmed** (point 3 below).

A purge is itself an audited event, and who may purge is a permission.

---

## Relationship to the permissions model

`Permission` (READ / WRITE / MANAGE, `shared_folders_plan.md`) answers "who may technically touch
this object". GxP roles (author / reviewer / approver / QA) answer "in what capacity does this person
take responsibility". They are **orthogonal**: an approver needs only `READ` — they write nothing,
they sign.

So `shared_folders_plan.md` needs no change, and its **"sharing can never exceed `READ`" ceiling is
favourable to compliance — keep it**. GxP roles are an attribute of the approval workflow, carried by
the signable entity, and explicitly *not* a fourth `Permission` value (which that plan already
documents as a pressure to resist).

**One addition it does need**: Part 11 requires permission changes to be audited.
`gws_shared_folder_member` must therefore be an auditable entity like any other.

---

## Points to settle

### 1. Data produced outside compliance mode, referenced inside it ⚠ (most structural)

A compliance-mode project references a resource produced by a scenario run **outside** compliance
mode. This will happen constantly at any customer. Options: refuse the reference; warn; or accept
and mark it "uncontrolled origin" so the status propagates to anything derived from it.

Leaning toward the third — refusal makes the mode unusable on real labs, and a silent warning loses
the information. But propagation rules (does a result derived from uncontrolled data stay
uncontrolled forever? can it be requalified, by whom?) need to be defined, and this decision shapes
the data model.

### 2. Compliance-mode granularity — confirm

Per root entity with inheritance is the working assumption; "decide later" was accepted. To confirm:
which entities can be roots (project, folder, scenario?), how inheritance interacts with entities
referenced by several roots, and confirmation that the transition is irreversible.

### 3. Purge policy vocabulary

Is the document plan's `origin_type` sufficient to distinguish source from reproducible
intermediate, or is a dedicated retention class needed? Depends on point 1 as well: uncontrolled-origin
data probably cannot be purged on the same terms.

### 4. Approval workflow and roles ⚠ (deferred, in scope)

Two-person signature (author ≠ approver) is common in GxP and **is in scope**. It requires a way to
designate who may approve what, which the platform lacks (`UserGroup` is a flat three-level
hierarchy). Options: nominative designation by the app case by case (simple, does not scale), or
functional roles scoped to a perimeter (project / dossier).

Also to settle: whether a generic state machine is needed (draft → in review → approved → superseded,
states declared by the app) or just "sign an object"; and what a Part 11 signature must carry beyond
today's `validate()` — re-authentication at signing time, an explicit *meaning*, the signer's
readable name and timestamp rendered in the document, and a hash binding to the signed content
(hence the `content_hash` above).

**Delegation** (the approver is on leave) is suggested as out of scope for V1 — it is a classic
source of non-compliance when done badly — but the model should not close the door.

### 5. Anchor destination

Where anchors go, and how the separation of duties is enforced and demonstrated. Possibly the
simplest form: externalise the audit table itself, so it is not modifiable by a DBA. Left open
deliberately.

### 6. Single database vs one per module

The trail being one core table is an argument for option A of split plan point 12. To confirm as an
input to that decision.

### 7. Audit trail volume

Per-field before/after on every auditable write has a real storage cost, and the extra SELECT per
update has a latency cost. Both need measuring on a realistic lab before compliance mode is switched
on broadly. The serialisation contract (hash instead of value for large fields) is the main lever.

---

## Amendments to the other plans

### To apply in [modular_apps_split_plan.md](modular_apps_split_plan.md)

- Add this document to "Companion documents".
- **Points 1+2 (entity-type registry)** gain a sixth declared capability: **`auditable`**, alongside
  `taggable` / `navigable` / `shareable` / `indexable` / `activity_logged`. Note that
  `activity_logged` and `auditable` are **not the same thing** — the former describes the UI activity
  feed (`ActivityObjectType`, mergeable, best-effort), the latter the regulatory trail
  (insert-only, chained). The registry entry for `auditable` also carries the **serialisation
  contract** (which fields to audit, which to exclude, which to store as a hash).
- **Point 12 (single DB vs one per module)** gains an argument for **option A**: the audit trail is
  one core table, keyed by soft reference, and it must survive an app being uninstalled — which a
  per-app table cannot do. Traceability is not by itself decisive, but it should be recorded as an
  input to that decision.
- **Point 14 (persisted typing names change in the split)** gains a compliance consequence:
  replayability of a *validated* scenario depends on the alias mechanism planned there. If an old
  typing name cannot be resolved, a validated run is no longer reproducible — which is exactly the
  claim GxP relies on.
- **Point 7 / point 8 (app documents, file layer)**: the `content_hash` this plan needs for
  integrity and signature binding is the **same column** as the `promoted_content_hash` /
  dedup hash those points call for. One column, three uses — decide it once.

### To apply in [shared_folders_plan.md](shared_folders_plan.md)

- **`gws_shared_folder_member` and `gws_shared_folder_item` must be auditable entities.** Part 11
  requires changes to access rights to be audited, so granting, modifying and revoking access are
  audited actions like any other. This is an addition, not a change: the plan already records
  `created_by` / `created_at` on membership rows, but that is current state, not history.
- **The `Permission` vocabulary needs no change.** GxP functional roles (author / reviewer /
  approver / QA) are orthogonal to READ / WRITE / MANAGE — an approver needs only `READ`, since they
  sign rather than write. This plan therefore reinforces rather than contradicts the "closed
  vocabulary" stance and the pressure-to-add-a-fourth-level warning in its "Points to settle".
- **The "sharing can never exceed `READ`" ceiling is favourable to compliance — keep it.** It means
  a shared object cannot be modified through the sharing path, so the audit trail of an object's
  content has a single access path to account for.
- **Its ⚠ "Unresolved: list queries"** acquires a compliance dimension: if a list query can return
  objects the user may not open, that is an access-control gap Part 11 would treat as a finding, not
  merely a UX inconsistency.

### To apply in [document_management_plan.md](document_management_plan.md)

- **The index is rebuildable; the audit trail is not.** The plan's rule "deactivate an app = delete
  its index rows, reactivate = re-enumerate" must **not** be generalised to the audit trail, which
  is retained with orphaned `entity_type` values. Worth stating explicitly next to the
  rebuildability discussion, because the two mechanisms look alike (both are core tables keyed by
  soft `(entity_type, entity_id)` references) and a reader may assume the same lifecycle applies.
- **The settled `origin_type` vocabulary** (`UPLOADED | AUTHORED | GENERATED | IMPORTED | DERIVED`)
  is the candidate basis for retention policy — distinguishing irreplaceable source data from
  reproducible intermediates. Whether it is sufficient for that purpose is point 3 of this plan's
  "Points to settle".
- **`RichTextFileService`** (the third storage, no table, no tags, no index) holds note attachments
  and figures. Files with no `FSNodeModel` row can carry no `content_hash` and cannot be audited or
  integrity-checked. If note attachments are in a compliance perimeter, unifying that storage
  becomes a compliance prerequisite, not only a search one.

### To apply in [ai_agent_chat_plan.md](ai_agent_chat_plan.md)

- **The AI agent's writes are audited like any other caller.** Since intent is declared at service
  level (not at route level), MCP tool calls that mutate auditable entities are captured
  automatically — but they need an action context, and their intent rows should record that the actor
  was an agent acting on behalf of a user. In compliance mode, agent-initiated mutations are a
  likely candidate for either exclusion or mandatory human confirmation. To settle in that plan.

## Implementation order

Ordered so that each step has standalone value and nothing is blocked on an open decision.

1. **`content_hash` on `FSNodeModel`** — independent of everything else, serves dedup + integrity +
   signature binding. Do it now.
2. **The `auditable` capability in the entity-type registry**, with the serialisation contract.
   Depends on the registry (split plan points 1+2), which is a prerequisite of the document index
   too.
3. **The new audit trail table + the `Model` capture hook + `AuditContext`**, tolerant mode, no
   chaining yet. Delivers a real trail immediately.
4. **Close the audit leaks**: `skip_hook`, the ~8 bulk deletes, plus an architecture test. Must
   precede any compliance claim.
5. **Hash chaining + the CLI verifier**, then anchoring.
6. **Compliance mode**: soft delete, mandatory reason, strict context, DB account without
   `UPDATE`/`DELETE`.
7. **Signature and approval workflow** — after point 4 above is settled.

Environment-version freezing (ALCOA+) is independent and can be slotted anywhere.

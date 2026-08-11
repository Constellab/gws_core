# Inter-App Communication — Separate Databases, App API, Event Bus

> Design document, part of the modular refactor. It builds on
> [modular_apps_split_plan.md](modular_apps_split_plan.md) (registries, soft references, à-la-carte
> installation) and **amends** it — see "Amendments to the modular apps split plan" at the end, which
> lists every change to apply there. It settles point 12 (database topology) and provides the
> transactional guarantees point 3 leaves open.

## Purpose

The split into several apps (`gws_core`, `gws_workflow`, `gws_note`, `gws_form`, `gws_project`,
`gws_invest`…) only works if apps can collaborate **without importing each other**. Three needs, plus
one optional:

1. **Data isolation** — each app owns its database, yet must still display core data (a user's name and
   photo) and attach its own information to core entities.
2. **App API (RPC)** — an app calls a method of another app and waits for the answer, with SDKs for
   central apps.
3. **Events** — an app reacts to what happened in another app, without the emitter knowing who listens.
4. **Veto (optional, deferred)** — an app blocks an operation in another app because one of its own
   conditions is not met.

**All four must work across separate data labs / servers**, not only in-process. That constraint drives
every choice below: anything that only works in one process is rejected, even when it is simpler.

This is the target architecture, described directly — not a migration path. The migration cost is real
and stated at the end ("Migration of existing labs"), but it is not the subject of this document.

### Companion documents

- [modular_apps_split_plan.md](modular_apps_split_plan.md) — the app split this document serves.
- [document_management_plan.md](document_management_plan.md) — the document index, which becomes a
  **mandatory** component here: with separate databases it is the only way to query across apps.
- [shared_folders_plan.md](shared_folders_plan.md) — `EntityAccessProvider`, which every app API must
  re-check locally (see "Rights are re-checked by the provider").
- [app_discovery_and_activation_plan.md](app_discovery_and_activation_plan.md) — the capability
  registry below feeds the app discovery it describes.

---

## Guiding principles

Five rules the rest of the document applies mechanically.

1. **A database is written only by the app that owns it.** No app ever writes into another app's
   database — not even the event relay. This is what makes local and cross-lab behave identically.
2. **Every cross-app call is written as if it were remote.** Serialisable DTOs, no shared ORM object,
   no shared transaction, fallible, idempotent. In-process is only an optimisation of the transport.
3. **No FK crosses a database boundary.** Soft references only (`(entity_type, entity_id)` strings),
   as already proven by `tag/entity_tag.py`.
4. **Choose the weakest coupling that answers the need.** Local cache > event > RPC > veto, in that
   order. Each step up adds an availability dependency.
5. **Contracts are versioned and additive-only.** An API version and an event name are public
   contracts; two labs do not upgrade on the same day.

---

## 1. Separate databases

One MariaDB database per app (`gws_core`, `gws_workflow`, `gws_note`, `gws_form`, `gws_project`…). The
mechanism already exists — `AbstractDbManager.get_unique_name()` — gws_core simply never used it for
itself.

**Zero cross-database FK. Zero replicated core table.**

Core references become plain columns: `created_by_id CHAR(36)`, `folder_id CHAR(36)`, with no FK. The
integrity guarantee is lost on data that is in practice never deleted (a user is deactivated, not
deleted), which is an acceptable trade for the isolation.

### Decision: reconstructible caches, not replication

Point 12 of the split plan proposes to **duplicate and synchronise the core tables into each module
database** so local FKs keep working. **This document rejects that approach.** Building a home-made
replication engine to save a few FKs is the most expensive source of bugs available: silent divergence,
event ordering, bootstrap, repair tooling. Replaced by:

**A cache is a read-only local projection, rebuildable at any moment, never authoritative.**

That single property is what distinguishes it from replication: no permanent divergence is possible,
only staleness.

### Three kinds of duplicated column — do not mix them

The distinction matters because putting the wrong thing in a cache is a data-loss bug, not a display
glitch.

| | **Cache** | **Snapshot** | **App's own table** |
|---|---|---|---|
| Question answered | who is user X *now*? | who was the author *at the time*? | what does *my app* know about X? |
| Owner | core | the app | the app |
| On core update | must follow | **must not change** | irrelevant |
| On `cache rebuild` | wiped and refilled | untouched | untouched |
| Written by | sync layer only | business code, once | business code, freely |
| Example | avatar in a task list | author name on a signed BSA-AIR | `role = "chef de projet"` |

A field that must stay frozen (a signed record, an exported report) belongs on the business row as a
snapshot column. The cache will correctly overwrite it when the user renames themselves — which is the
bug.

### `CoreCacheModel` — provided by the core, not hand-rolled per app

Every app needs this for users, folders and tags. Per-app copies would drift, so the core provides the
base class and the app declares only which fields it wants:

```python
@core_cache("core.user", version=1)
class UserCache(CoreCacheModel):
    """Read-only local projection of core users. Rebuildable at any time."""
    user_id    = CharField(primary_key=True)
    first_name = CharField(null=True)
    last_name  = CharField(null=True)
    email      = CharField(null=True)
    photo_url  = CharField(null=True)
    is_active  = BooleanField(default=True)

    fields_from_core = ["first_name", "last_name", "email", "photo_url", "is_active"]
    ttl = timedelta(hours=24)          # lazy-refresh threshold
```

The decorator provides, identically in every app: the event subscription, the bootstrap, the lazy batch
fill, the rebuild CLI, and read-only enforcement.

**Three filling paths, all required:**

1. **Bootstrap** — on app install, one paginated core call fills the table.
2. **Events** — `core.user.updated.v1` / `core.user.deactivated.v1` update the row. Steady state.
3. **Lazy fill on miss** — a row absent or older than `ttl` triggers a *batched* core call (never N+1).
   This is the safety net: if the relay is down for an hour, the UI still shows correct names. Without
   it, an event gap is a visible bug.

**The rebuild is the acceptance test:**

```bash
gws app cache rebuild --app project --cache user
```

`TRUNCATE` + refill from core. **If that command cannot be run safely at any moment, it is not a cache
and a replication engine has been built by accident.**

### Three rules that keep caches from rotting

- **Projection only, never a filter.** `WHERE user_cache.email LIKE '%x%'` couples business results to
  cache freshness — a stale row silently changes which rows a user sees. Filter on `user_id` (owned
  locally), then decorate with the cache. This is the rule that gets broken first.
- **`LEFT JOIN`, never `INNER`.** A user missing from the cache (new, or mid-rebuild) must not make the
  business row disappear. `LEFT JOIN` shows the row with an empty name, which is far safer.
- **No FK to a cache table, even within the same database** — it gets truncated. This is the one
  intra-database FK to forbid.
- **Cache rows survive deactivation.** Sync `is_active` and let the UI grey the user out; never delete
  cache rows, or historical authorship renders blank.

### The app's own data about a core entity

Anything that only makes sense inside the app (role, quota, preferences, join date) is a normal business
table the app owns:

```sql
-- app's own table: survives rebuild, app writes it freely
project_member(
  id CHAR(36) PRIMARY KEY,
  project_id CHAR(36) NOT NULL,   -- local FK: fine, same database
  user_id    CHAR(36) NOT NULL,   -- no FK: neither to core nor to user_cache
  role       VARCHAR(50) NOT NULL,
  joined_at  DATETIME NOT NULL,
  UNIQUE(project_id, user_id)
)
```

Joining it with the cache is **local and free** — that is the point of the cache living in the app's own
database:

```sql
SELECT pm.role, uc.first_name, uc.last_name, uc.photo_url
FROM project_member pm
LEFT JOIN user_cache uc ON uc.user_id = pm.user_id
WHERE pm.project_id = ?
```

What is lost is the JOIN towards **another app**, not towards the core.

### The photo, specifically

If `photo_url` points at the core, every app's UI hard-depends on the core being reachable to render an
avatar — and cross-lab, that URL may be unreachable entirely. Decision: **store the URL for same-server
apps** (a broken avatar is cheap, a broken page is not), **copy the bytes into the app's filestore for
cross-lab apps**.

### Consequence: the document index becomes mandatory

With separate databases, a cross-app JOIN is impossible. Every cross-app query — dashboards, global
search, `EntityLink` traversal — goes through the document index of
[document_management_plan.md](document_management_plan.md), fed by events. **That index is no longer a
convenience; it is the only cross-app query path.** Tables that are transverse by nature (`EntityLink`,
`EntityTag`, the document index) live in the core database and never join an app table.

---

## 2. App API (RPC)

"RPC" here means only: an app calls a method that executes elsewhere and waits for the answer. It is
the opposite of an event.

| | **RPC** | **Event** |
|---|---|---|
| Form | `x = project.get_task(id)` | `EventBus.publish(...)` |
| Caller waits | yes, blocked | no |
| Returns | a value | nothing |
| If target is down | **immediate failure** | processed later, nothing lost |
| Who knows whom | caller knows the target | emitter ignores its subscribers |

### The contract

The provider declares its public API; the consumer resolves it by name and version, never by importing
the app:

```python
# gws_project/api/project_api.py
@app_api(name="project", version=1)
class ProjectApi(AppApi):
    """Public API of gws_project. Versioned contract: never break within v1."""

    @api_method(read_only=True)
    def get_task(self, task_id: str) -> TaskDTO: ...

    @api_method(read_only=True)
    def list_tasks(self, project_id: str, page: int = 0, size: int = 50) -> PageDTO[TaskDTO]: ...

    @api_method(mutating=True)
    def complete_task(self, task_id: str, idempotency_key: str) -> TaskDTO: ...
```

```python
# app_b — imports the SDK, never gws_project
project = AppClient.get("project", version=1)
task = project.complete_task(task_id="t-42", idempotency_key=str(uuid4()))
```

`AppClient.get()` queries the capability registry and returns a typed proxy. If the app is absent it
raises `AppNotAvailableError`, which the consumer catches to degrade gracefully — consistent with
à-la-carte installation.

Each `@api_method` is automatically exposed as a FastAPI endpoint
(`/api/app/{name}/v{version}/{method}`) with the same signature. One implementation, two access paths.

### Two transports, invisible to the caller

```
AppClient.get("project", v1)
    ├─ InProcessTransport   same server  → direct call + forced DTO round-trip
    └─ HttpTransport        other lab    → POST /api/app/project/v1/complete_task
```

**Non-negotiable: `InProcessTransport` serialises anyway.** Arguments are validated into DTOs and so is
the return value. It costs tens of microseconds and guarantees that no code relies on a shared ORM
object, a Peewee lazy-load or a shared transaction. Without that round-trip, code works locally and
breaks on the first remote call — six months later, when it is expensive to fix.

### Decision: SDK per provider, generated

`app_b` imports `gws_project_sdk` (DTOs + typed client). **Depending on a versioned SDK is not
depending on the app** — the SDK contains no business logic and no ORM.

```bash
gws sdk generate --app project --version 1 --out ./sdk
```

Generated from the OpenAPI schema that `@api_method` already produces, versioned with the app, published
as a package for central apps. A hand-written SDK drifts from its server within months.

### What the transport always propagates

```
X-Trace-Id          end-to-end correlation (RPC + events)
X-User-Id           the originating user's identity
Authorization       calling lab's api-key (cross-lab only)
X-Calling-App       who is calling — audit and debugging
X-Idempotency-Key   on mutating methods
```

The `api-key` (lab) + `X-User-Id` (user) pair is the model already used by `ExternalLabAuth` and is kept
everywhere.

### Rights are re-checked by the provider

**The provider never trusts the caller about permissions.** `gws_project` re-checks with its own
`EntityAccessProvider` ([shared_folders_plan.md](shared_folders_plan.md)) on every call. Otherwise any
app becomes a way to bypass access control.

### Idempotency on mutating methods

Every `mutating=True` method requires an `idempotency_key`. The provider keeps, in **its own** database:

```sql
api_idempotency(
  idempotency_key VARCHAR(255) NOT NULL,
  app_name        VARCHAR(100) NOT NULL,   -- the caller
  method          VARCHAR(255) NOT NULL,
  PRIMARY KEY (idempotency_key, app_name, method),
  request_hash    CHAR(64) NOT NULL,       -- detects key reuse with a different payload
  response        JSON NOT NULL,           -- replayed as-is on duplicate
  created_at      DATETIME NOT NULL
)
```

- Key seen + same `request_hash` → return the stored response, do not re-execute.
- Key seen + different hash → `409 Conflict`. That is a caller bug and must not be absorbed silently.

This is what makes retrying after an HTTP timeout safe. Without it, a network timeout on
`complete_task` leaves the caller unable to know whether the task completed, and a naive retry doubles
the effect.

### Capability registry

A table in the core database, filled at each brick's boot:

```sql
app_capability(
  app_name    VARCHAR(100) NOT NULL,
  version     INT NOT NULL,
  PRIMARY KEY (app_name, version),
  methods     JSON NOT NULL,
  schema_hash CHAR(64) NOT NULL,
  location    ENUM('LOCAL','REMOTE') NOT NULL,
  base_url    VARCHAR(512) NULL,
  lab_id      CHAR(36) NULL,
  status      ENUM('UP','DOWN','UNKNOWN') NOT NULL DEFAULT 'UNKNOWN',
  last_check  DATETIME NULL
)
```

Three uses: resolving `AppClient.get()`; answering the `capabilities` endpoint the frontend needs (point
11 of the split plan); and **detecting contract mismatch at boot** — if a consumer's expected
`schema_hash` differs from the provider's, boot fails rather than the first production call.

### Versioning

An API version is **additive-only**: a method or an optional field may be added; nothing may be removed
or change type. A breaking change creates `v2`, and both coexist until consumers migrate. Mandatory for
cross-lab, where two labs never upgrade simultaneously.

### When *not* to use RPC

A synchronous RPC creates an **availability coupling**: if `gws_project` is down, the caller is blocked.

| Need | Mechanism |
|---|---|
| Read fresh data, now | **RPC** |
| React to a change | **Event** |
| Display a name, a photo | **Local cache** (§1) |
| Trigger an action in another app | **Event**, not RPC |

The classic mistake is calling another app by RPC on every page render. Three apps doing that and
latency becomes the sum of latencies while availability becomes the product of availabilities.
Mandatory on the HTTP transport: **short timeout (2–5 s) and a circuit breaker** — otherwise one slow
app propagates its slowness to the whole lab.

---

## 3. Events

### Why an outbox, independently of the transport

Without an outbox, publishing means writing to two systems with no common transaction (*dual write*):

```python
task.save()                      # MariaDB commit
broker.publish(TaskDoneEvent)    # ← crash here: task is DONE, event never exists
```

Both orderings are broken, and **no broker can fix it** — the flaw is between the two calls. The outbox
fixes it by writing the event *inside* the business transaction, so event and state change commit
together or not at all.

**Consequence: the outbox is mandatory whatever the transport.** Redis, Kafka or a plain `SELECT` are
choices about *how the event travels*, not about this guarantee. Removing the outbox because "there is a
broker now" reintroduces dual-write.

### Decision: pull mode

Each consumer **reads** the outboxes it subscribes to and writes only into its own database.

```
        LAB 1                                     LAB 2
┌──────────────────────┐                 ┌────────────────────────┐
│ gws_project          │                 │ app_b                  │
│  project_task        │                 │  worker app_b ──┐      │
│  event_outbox        │                 │                 │      │
│    offset 99 ────────┼── HTTP pull ────┼─────────────────┘      │
│  GET /events/pull    │◄────────────────┤  event_inbox           │
└──────────────────────┘                 │  event_cursor          │
                                         │    lab1:project → 99   │
                                         └────────────────────────┘
```

Rejected alternative — **push**, where the emitter's relay writes into every subscriber's database:
simpler to start, but it violates principle 1 (a database is written only by its app) and **does not
survive cross-lab** — a remote app can never have write access to the provider's database. Pull is
identical locally and remotely, which is the whole point.

Consequences of pull, all beneficial:

- **The emitter needs no configuration.** It exposes a journal; it does not know who reads, stores no
  per-subscriber position, declares nothing. Adding a subscriber changes nothing on its side.
- **The cursor lives with the consumer**, so each app advances at its own pace. A lab switched off for a
  week catches up on restart.
- **A network outage is a non-event**: the pull fails, the cursor does not move, it retries. Nothing
  lost, nothing duplicated.
- **A consumer behind a firewall works.** With no public IP, a client lab can still consume another
  lab's events. Push makes that impossible — decisive for a product deployed at customer sites.

### Schema

```sql
-- ════════ EMITTER's database (gws_project) ════════
-- Append-only journal. No status column: the emitter ignores who reads.
CREATE TABLE event_outbox (
  offset        BIGINT AUTO_INCREMENT PRIMARY KEY,   -- monotonic read order
  event_id      CHAR(36) NOT NULL UNIQUE,            -- stable identity (idempotency)
  event_name    VARCHAR(255) NOT NULL,               -- 'project.task.done'
  version       INT NOT NULL DEFAULT 1,
  partition_key VARCHAR(255) NOT NULL,               -- entity_id: per-entity ordering
  payload       JSON NOT NULL,                       -- SELF-SUFFICIENT
  occurred_at   DATETIME(6) NOT NULL,
  trace_id      CHAR(36) NULL,
  triggered_by  CHAR(36) NULL,                       -- user_id, no FK
  causation_id  CHAR(36) NULL,                       -- event that caused this one
  causation_depth INT NOT NULL DEFAULT 0,
  INDEX idx_name (event_name, offset),
  INDEX idx_purge (occurred_at)
);

-- ════════ CONSUMER's database (app_b) ════════
CREATE TABLE event_cursor (
  source       VARCHAR(255) NOT NULL,   -- 'local:project' | 'lab1:project'
  consumer     VARCHAR(255) NOT NULL,   -- 'app_b.budget_closer'
  last_offset  BIGINT NOT NULL DEFAULT 0,
  updated_at   DATETIME(6) NOT NULL,
  PRIMARY KEY (source, consumer)
);

-- Local work queue. The PK IS the idempotency guarantee.
CREATE TABLE event_inbox (
  event_id      CHAR(36) NOT NULL,
  consumer      VARCHAR(255) NOT NULL,
  PRIMARY KEY (event_id, consumer),              -- rejects any duplicate
  source        VARCHAR(255) NOT NULL,
  event_name    VARCHAR(255) NOT NULL,
  version       INT NOT NULL,
  partition_key VARCHAR(255) NOT NULL,
  payload       JSON NOT NULL,
  occurred_at   DATETIME(6) NOT NULL,
  trace_id      CHAR(36) NULL,
  received_at   DATETIME(6) NOT NULL,
  status        ENUM('PENDING','DONE','FAILED') NOT NULL DEFAULT 'PENDING',
  attempts      INT NOT NULL DEFAULT 0,
  next_retry_at DATETIME(6) NULL,
  last_error    TEXT NULL,
  INDEX idx_work (status, next_retry_at),
  INDEX idx_order (partition_key, occurred_at)
);

-- Terminal failures, replayable from an admin UI.
CREATE TABLE event_dead_letter (
  event_id   CHAR(36) NOT NULL,
  consumer   VARCHAR(255) NOT NULL,
  PRIMARY KEY (event_id, consumer),
  source     VARCHAR(255) NOT NULL,
  event_name VARCHAR(255) NOT NULL,
  version    INT NOT NULL,
  payload    JSON NOT NULL,
  trace_id   CHAR(36) NULL,
  attempts   INT NOT NULL,
  last_error TEXT NOT NULL,
  failed_at  DATETIME(6) NOT NULL,
  replayed_at DATETIME(6) NULL
);
```

### Publishing — inside the business transaction

```python
@transaction()
def complete_task(task_id: str) -> Task:
    task = Task.get_by_id(task_id)
    task.status = TaskStatus.DONE
    task.save()
    EventBus.publish(TaskDoneEvent(          # INSERT event_outbox, same transaction
        task_id=task.id,
        project_id=task.project_id,
        task_title=task.title,               # self-sufficient payload
        completed_by=CurrentUserService.get_id(),
        completed_at=task.updated_at,
    ))
    return task
```

`publish()` **must raise if no transaction is active** — the only real protection against dual-write
creeping back in. The caller's latency does not depend on how many apps listen: no network call, no
listener executed, no thread started.

**Payloads are self-sufficient.** An event carrying only an id forces every consumer to call back by
RPC — reintroducing the availability coupling pull just removed — and worse, it reads the *current*
state, which may have changed. An event carries the state as of when it happened.

### Fetching — one worker task per (source, consumer)

```python
cursor = EventCursor.get(source, consumer)
envelopes = source.fetch(after=cursor.last_offset, limit=100)   # Db | HttpPull | Redis

with transaction():                             # app_b's database only
    for env in envelopes:
        EventInbox.insert_ignore(env, consumer)      # duplicate → ignored by the PK
    cursor.last_offset = envelopes[-1].offset
    cursor.save()
```

One local commit makes it **impossible to advance the cursor without having stored the events**. A crash
before commit means re-reading, and the PK absorbs it.

### Processing — atomic with the business write

```python
@transaction()
def process(row: EventInbox):
    try:
        handler(row.payload)             # app_b's business write
        row.status = 'DONE'
    except RetryableError as e:
        row.attempts += 1
        row.last_error = str(e)
        if row.attempts >= MAX_ATTEMPTS:             # 5
            DeadLetter.create_from(row)
            row.status = 'FAILED'
        else:
            row.next_retry_at = now() + backoff(row.attempts)   # 1s, 4s, 16s, 1m, 5m
    row.save()
```

Business write + `DONE` marking in **the same transaction, the same database**: that is what makes the
*effect* exactly-once despite at-least-once delivery. Handlers must still be written as replayable.

### Ordering

The worker does not process a row while an **earlier** row with the same `partition_key` is still
`PENDING`. This guarantees `created → updated → deleted` order per entity without imposing a global
order, which would be expensive and pointless.

For an event touching many entities (e.g. "project archived" affecting 50 tasks), `partition_key` is the
root entity, and ordering is only guaranteed relative to it.

### Transports

```python
class EventSource(ABC):
    @abstractmethod
    def fetch(self, after: int, limit: int) -> list[EventEnvelope]: ...
```

| Source | Read | Cursor | Use |
|---|---|---|---|
| `DbSource` | `SELECT ... WHERE offset > ?` | `event_cursor` | local, default |
| `HttpPullSource` | `GET /api/events/pull?after=…` | `event_cursor` | cross-lab, mandatory |
| `RedisSource` | `XREADGROUP BLOCK` | held by Redis | optional, latency only |

**Decision: ship `DbSource` + `HttpPullSource`, no Redis.** Cross-lab requires the HTTP pull anyway, and
`DbSource` is roughly 50 further lines once the pull exists — one single concept (an ordered journal read
with a cursor), zero infrastructure dependency imposed on every customer lab.

Redis remains available later, and it changes nothing in the apps: the `@subscribe` declarations are
untouched. Two facts to keep in mind:

- **Redis does not help cross-lab.** A stream is local to a lab; exposing it across servers is not
  viable (attack surface, no per-event ACL, firewalled consumers). Deploying Redis therefore means
  running **two transports at once** — Redis locally, HTTP pull for remote labs — which is another
  reason to keep `EventSource` as the seam.
- **Redis holds the cursor itself**, unlike the other two. Switching transport means transferring the
  position; done carelessly it either replays (absorbed by the inbox PK) or skips (a real gap).

### Polling interval

Local `DbSource`: ~1 s (business events tolerate it; 200 ms is available if ever needed). Cross-lab
`HttpPullSource`: 30 s, tunable per source. Slower is explicitly fine — nothing in the design depends on
low latency, and a slow poll costs nothing but freshness.

### Worker deployment

**Decision: one `gws events worker` process**, handling every (source, consumer) pair as concurrent
tasks — logical isolation, one process to deploy. Separate from the FastAPI process: otherwise a server
restart or an HTTP traffic spike starves event processing, and the two cannot be scaled independently.

### Subscription

```python
@subscribe("project.task.done", version=1, consumer="app_b.budget_closer")
def on_task_done(event: TaskDoneEventDTO) -> None:
    BudgetService.close(event.task_id)      # replayable: at-least-once
```

`consumer` is a stable logical name. **Never rename it**: it is the key of both the cursor and the
inbox, so renaming replays the whole history from offset 0. Two listeners of the same app on the same
event get one row, one retry chain and one DLQ entry each.

### The cross-lab endpoint

```
GET /api/events/pull?app=project&after=98&limit=100
Authorization: api-key <calling lab's key>
```

**ACL filtering is mandatory** — the outbox holds complete business payloads, so without it this
endpoint is a data leak:

```sql
-- provider's core database
event_subscription_acl(
  lab_id     CHAR(36) NOT NULL,
  event_name VARCHAR(255) NOT NULL,
  PRIMARY KEY (lab_id, event_name),
  granted_at DATETIME NOT NULL,
  granted_by CHAR(36) NOT NULL
)
```

The query returns only event names explicitly granted to that `lab_id`. **Default: nothing is granted.**

### Decision: long retention

The outbox is a **long-lived audit journal**, not a transient queue. Rationale: replaying history from
offset 0 is how a newly installed app builds its caches (§1) and how the document index is rebuilt —
both of which are load-bearing in this architecture.

Retention is per event name, declared with the event:

- **Long (indefinite / years)** — structural events: `*.created`, `*.deleted`, status transitions,
  anything a projection is rebuilt from.
- **Short (30–90 days)** — high-volume, low-value events, where a rebuild would use a full RPC resync
  instead.

Volume is manageable: the payload is a JSON row, and a partition or archive strategy on `occurred_at`
handles growth. Purging structural events would silently forfeit rebuildability, which is worth far
more than the disk.

### Gap detection

A consumer whose cursor falls behind the oldest available offset must **fail loudly**:

```python
if cursor.last_offset < source.get_min_available_offset():
    raise EventGapError(source, consumer, cursor.last_offset)
```

This alerts and requires an intervention (projection rebuild, RPC resync). It must never silently resume
at the oldest available offset.

### Event loops

`app_b` reacts to a `project` event by writing, which emits an event `project` listens to, and so on.
Cheap to prevent now, very painful to debug later: `causation_id` + `causation_depth` in the envelope,
incremented on every event emitted while handling another, with a cap (10) that stops and alerts. The
`trace_id` then reconstructs the chain.

### Event naming and versioning

`{app}.{entity}.{action}` + version: `project.task.done` v1. An event name is a **public contract**,
harder to change than an API because the emitter does not know who listens. Additive-only within a
version; a breaking change is a new version, and the emitter publishes both until consumers migrate.

---

## 4. Veto / `DecisionHook` — optional, deferred

**Not to be implemented now.** Recorded because the insertion point is cheap to reserve and expensive to
retrofit.

### The need

An app blocks an operation in another app that does not know it exists: `gws_project` moves a task to
DONE, and `app_b` must prevent it because one of its conditions fails.

### Why this is not an event

An event is a **completed fact** (`TaskDone`); this is a **question about the future** (`may I?`).
Conflating them is the classic mistake:

| | Event | Decision hook |
|---|---|---|
| Semantics | it happened | may I? |
| Emitted | after commit | before, in the transaction |
| Returns | nothing | `ALLOW` / `DENY(reasons[])` / `ERROR` |
| Participant crashes | logged, ignored | must decide (declared policy) |
| Replayable | yes, idempotent | no, side-effect free |

The current `EventDispatcher` conflates them: a synchronous listener raising an exception blocks the
caller (`is_synchronous() -> True`, used by `form_note_cascade_listener.py`). That works in-process but
is a dead end as a foundation: an exception carries no aggregated reasons, cannot distinguish "refused"
from "crashed", and means nothing across a network boundary.

### The design when implemented

```python
@decision_hook("project.task.can_complete", version=1)
class CanCompleteTask(DecisionHook):
    task_id: str
    project_id: str
    on_error = FailPolicy.CLOSED      # declared by the hook, not the participant
    timeout_ms = 2000

@hook_participant("project.task.can_complete", version=1)
def check_budget(hook: CanCompleteTask) -> Decision:
    if not BudgetService.is_covered(hook.task_id):
        return Decision.deny("Budget not validated", code="BUDGET_MISSING",
                             resolve_url=f"/budget/{hook.task_id}")
    return Decision.allow()
```

```python
verdict = HookBus.ask(CanCompleteTask(task_id=..., project_id=...))
if verdict.denied:
    raise ForbiddenException(verdict.format_reasons())   # all reasons, aggregated
```

Rules: `ask()` is **read-only** (a refusal must leave no side effects — enforced by a read-only
transaction plus tests); three outcomes with an explicit `on_error` policy per hook; a hook name is a
versioned public contract.

### Constraints

- **Local only.** A remote veto creates an availability coupling: with several apps vetoing each other,
  nothing moves as soon as one node is down, and unblocking requires understanding all of them.
- **Cross-lab: use state, not a veto.** The other app pushes a state (`blocked=true, reason=…`) that the
  owner stores locally and reads in O(1). A fragile synchronous call becomes a local read.
- **Advisory, not transactional.** Between `ask()` and commit, the condition may change. For truly
  critical constraints (money, stock) the participant must also enforce it on its own side. Never
  present the hook as a cross-app transactional guarantee.

### What to reserve now

`TaskService.complete()` calls `HookBus.ask()`, which with no registered participant returns `ALLOW` at
no cost. The insertion point exists; the mechanism comes later.

Meanwhile, the pushed-state pattern already covers the `gws_project` / `app_b` case with no availability
coupling, and is often sufficient.

---

## Cross-cutting concerns

### Observability

Not covered by any of the five existing documents, and it decides whether the system is operable in
production. An event → handler → RPC chain across three apps is undebuggable without correlation.

- **`trace_id` propagated end to end**, across RPC *and* events (`X-Trace-Id`, `event_outbox.trace_id`,
  `event_inbox.trace_id`), including when an RPC triggers an event that triggers an RPC.
- **Admin UI** over outbox / cursors / inbox / DLQ: what is late, what is failing, replay a dead letter.
  With `DbSource` this is a `SELECT`, which is a genuine advantage of not starting with a broker.
- **Metrics per (source, consumer)**: cursor lag, inbox depth, retry rate, DLQ count. Cursor lag is the
  single most useful alert in the whole system.
- **`gws db query`** keeps working per app database (`--db gws_project`), so inspection is available with
  no extra tooling.

### Migration of existing labs

Real cost, and the bulk of the actual work — stated here, out of scope for this document:

- Moving tables between databases (all app tables leave the `gws_core` database).
- Dropping every cross-brick FK and turning it into a plain column.
- Rewriting persisted typing names (point 14 of the split plan).
- Initial cache bootstrap in each app database.
- Backfilling the outbox if projections must be rebuilt from history.

### Architecture enforcement

Extends point 13 of the split plan. Automated, in CI:

- **No app→app import** (import-linter contracts).
- **No cross-database FK**, checked against the declared schema.
- **No `publish()` outside a transaction** (test + runtime assertion).
- **No FK to a `CoreCacheModel` table.**
- **No cache column used in a `WHERE` filter** — the hardest to automate, the most valuable; at minimum
  a review checklist item.
- **Boot matrix**: start the server with each app combination, verifying `AppNotAvailableError`
  degradation.

---

## Amendments to the modular apps split plan

To apply in [modular_apps_split_plan.md](modular_apps_split_plan.md):

1. **Point 12 (database topology) — settled: option B, one database per app.** The proposal to
   *duplicate and synchronise the core base tables into each module database* is **rejected** and
   replaced by §1 here: FK-free plain columns + `CoreCacheModel` reconstructible caches. Replace the
   "Core base tables" paragraph accordingly.
2. **Point 12 — the document index becomes mandatory.** With no cross-app SQL, the index of
   [document_management_plan.md](document_management_plan.md) is the only cross-app query path, not a
   convenience.
3. **Point 3 (`EntityLink` reconciliation) — the transactional guarantee it leaves open is answered
   here**: reconciliation listeners run through the inbox (§3), so they are idempotent by PK, retried
   with backoff, and dead-lettered instead of lost. Its "events are in-process today; what happens on
   partial failure?" is resolved by outbox + inbox.
4. **The event bus (`model/event/`) is superseded** by §3 for anything crossing an app boundary. The
   in-process dispatcher may remain for intra-app listeners, but its synchronous-listener-as-veto
   pattern (`form_note_cascade_listener.py`) is what §4 replaces — and §4 is deferred, so
   cross-app cascade deletes must go through `EntityLink` deletion policies, not a sync listener.
5. **Point 13 (architecture enforcement)** — extended with the four additional automated checks listed
   above.
6. **New: observability** is a first-class requirement, absent from all five documents.

---

## Summary of decisions

| # | Subject | Decision |
|---|---|---|
| 1 | Database topology | One per app; zero cross-DB FK; no replicated core table |
| 1 | Core data in apps | `CoreCacheModel`, reconstructible, projection-only, `LEFT JOIN` |
| 1 | App data on a core entity | The app's own business table (`project_member.role`) |
| 1 | Frozen historical values | Snapshot column on the business row, never a cache |
| 1 | Cross-app queries | Document index (mandatory), never a JOIN |
| 2 | Cross-app calls | `AppApi` / `AppClient`, resolved by name + version |
| 2 | Transports | `InProcess` (forced DTO round-trip) and `Http` |
| 2 | Consumer dependency | Generated, versioned per-provider SDK |
| 2 | Mutations | `idempotency_key` + `api_idempotency` table, `409` on hash mismatch |
| 2 | Permissions | Re-checked by the provider, never trusted from the caller |
| 3 | Atomicity | Transactional outbox, mandatory whatever the transport |
| 3 | Distribution | **Pull**: the consumer reads, writes only its own database |
| 3 | Idempotency | `event_inbox` PK `(event_id, consumer)` |
| 3 | Failures | Backoff ×5 then dead-letter, replayable |
| 3 | Ordering | Per `partition_key`, no global order |
| 3 | Transports | `DbSource` + `HttpPullSource`; Redis optional, latency only |
| 3 | Polling | ~1 s local, 30 s cross-lab; slower is fine |
| 3 | Workers | One `gws events worker` process, outside FastAPI |
| 3 | Retention | Long, per event name; structural events kept for rebuildability |
| 3 | Cross-lab security | Per-`(lab_id, event_name)` ACL, deny by default |
| 4 | Veto | Designed, **deferred**; reserve `HookBus.ask()` returning `ALLOW` |
| — | Observability | `trace_id` end to end + admin UI on outbox/inbox/DLQ |

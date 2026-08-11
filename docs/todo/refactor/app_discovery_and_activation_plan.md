# App Discovery & Activation — design context document

> Base context for a design session. Self-contained: it does not assume the reader has read the
> other plans, but it builds on [modular_apps_split_plan.md](modular_apps_split_plan.md) (the
> technical enabler) and connects to [ai_agent_chat_plan.md](ai_agent_chat_plan.md) (AI-assisted
> discovery) and `gws_ai_toolkit/docs/todo/rag_embedded_stack_implementation_plan.md` (the Search
> app).

## Purpose & scope

The platform is being refactored so that every major functionality becomes an **independent app**
that users activate and use — without ever seeing a datalab, a brick, or an installation procedure.

This document covers **discovery** (how a user finds the app that answers their need) and
**activation** (what happens between "Activate" and "the app is visible and ready"), ending at the
moment the app's entry points appear in the user's workspace.

**Explicitly out of scope:**

- App **configuration and runtime** (starting/serving the apps, per-app settings) — a later
  document.
- The **publication pipeline** (where published apps come from, who validates them, which registry
  hosts them) — the existing sharing/publication channels are being reconsidered; this document only
  assumes that *published app definitions exist somewhere* and stays agnostic about the channel.
- The current feature set of the user-facing platform — it will change substantially; everything
  here describes the **target**, not the existing product.

## Problem statement

Today, using an app requires the user to understand and execute a technical chain:

```
create a datalab → configure a brick → start the app → share it
```

Every step exposes an implementation concept (datalab, brick, app instance). The target experience
is:

```
find the app that matches my need → Activate → use it
```

Two distinct problems to solve:

1. **Discovery** — shared objects exist today but are organized by *technical object type*, not by
   *user need*. A user who wants "to write a report on my analysis results" has no way to find out
   that the Note app does that.
2. **Activation** — the entire technical chain (runtime provisioning, brick installation,
   registration) must collapse into a single user-facing verb, executed by an orchestrator.

## Vocabulary: two layers that never mix

| User-facing concept | Hidden technical reality |
|---|---|
| **App** — a product with a name, an icon, use cases | One or more **bricks** at pinned versions |
| **Use case / entry point** — "Write and share a note" | A route inside an app + capability requirements |
| **Activate** | Provision/resolve a datalab, install bricks, run migrations, register capabilities |
| **Workspace** — where the user works and launches things | One or **several datalabs** (topology invisible) |
| **"New…" launcher** | Entry-point catalog × active capabilities |

The golden rule of this document: **nothing from the right column ever appears in the user
experience**. (An expert/advanced view may still expose it for power users and operators — see
points to settle.)

## Foundation: the modular split

The [modular apps split](modular_apps_split_plan.md) breaks the `gws_core` monolith into a technical
**core** (users/auth, DB, files, tags, rich text engine, registries, event bus, app engine) plus
independent **app bricks** (`gws_workflow`, `gws_note`, `gws_form`, …) with three hard properties:

- **À-la-carte installability** — a lab can run with only `gws_note`, or only `gws_workflow`. This
  is precisely what makes "Activate Note" = "install `gws_note`" possible and cheap.
- **No app→app imports** — cross-app collaboration goes through core-owned mechanisms only:
  registries (sync), events (async), soft `(entity_type, entity_id)` references (`EntityLink`).
  This is what makes any *combination* of activated apps valid.
- **Graceful degradation** — content referencing an absent app stays intact (opaque JSON) and
  renders as an "unavailable" placeholder; activating the app later restores it. This is what makes
  *de*activation safe.

A core **capabilities endpoint** lists which apps are active — the same source of truth drives both
the activation state in the store and the entry points shown in the launcher.

## The App Manifest — the missing object

Discovery and activation both hinge on one new first-class object: the **App**, described by a
manifest with two faces.

- **User-facing half** (feeds discovery): name, icon, tagline, need-oriented description,
  screenshots, categories, and a list of **entry points** — short, need-phrased use cases.
- **Technical half** (feeds activation, never shown): providing brick(s) + pinned versions,
  required core version, dependencies on other apps, entry-point routes, contributed extension
  registrations.

Illustrative schema (final format to settle):

```yaml
app: note
name: "Note"
tagline: "Write, document and share"
categories: [document-and-share]
bricks:
  - { name: gws_note, version: "1.2.0" }
requires: []                    # hard app dependencies (activation refuses/co-activates)
enhanced_by: [workflow, form]   # optional: extra features light up when these are active
entry_points:
  - key: write-note
    title: "Write and share a note"
    description: "Write a rich document and share it by link with collaborators or clients."
    keywords: [note, document, write, share, memo]
    category: document-and-share
    route: /note/new
    requires: []
  - key: report-from-results
    title: "Create a report from analysis results"
    description: "Assemble charts and result views produced by your analyses into a shareable report."
    keywords: [report, results, charts, deliverable]
    category: document-and-share
    route: /note/new?mode=report
    requires: [workflow]        # this entry point only exists if Workflow is active
```

Key modelling choices baked into this schema:

- **Entry points are first-class**, not a property buried in a description. They are the unit of
  discovery (users search for outcomes, not apps) and the unit of the launcher.
- **Two dependency strengths.** `requires` is hard: activation must ensure the dependency is active
  (or co-activate it). `enhanced_by` is soft: nothing to install; the feature simply appears when
  both apps happen to be active — this maps 1:1 onto the split's graceful-degradation and registry
  mechanics.
- **`requires` can be scoped per entry point**: the Note app itself needs nothing, but its
  "report" entry point needs Workflow. The app is activatable alone; the entry point stays hidden
  (or shown as "requires Workflow") until Workflow is active.

## The example catalog (5 apps)

These five apps are the running example of the whole document. Together they exercise every
dependency shape: fully standalone, hard `requires`, soft `enhanced_by`, and the N-way provider
pattern.

### 1. Workflow (`gws_workflow`)

The data-analysis engine: scenarios, protocols, tasks, resources, views. The direct product of the
split's biggest brick.

| Entry point | Requires | Notes |
|---|---|---|
| "Run an analysis on my data" | — | upload data, pick a pipeline, run |
| "Build an analysis pipeline" | — | protocol editor |
| "Browse my data and results" | — | resource explorer |

- Bricks: `gws_workflow`. Dependencies: none — standalone.
- Special role: several *other* apps' entry points declare `requires: [workflow]` or are
  `enhanced_by` it. Workflow itself never depends on anyone.

### 2. Note (`gws_note`)

Rich documents: notes, reports, templates.

| Entry point | Requires | Notes |
|---|---|---|
| "Write and share a note" | — | works on a lab with only `gws_note` |
| "Create a report from analysis results" | `workflow` | embeds resource views into the document |

- Bricks: `gws_note`. Dependencies: none hard at app level; `enhanced_by: [workflow, form]`.
- Illustrates the **canonical cross-app mechanism**: Workflow registers the `resourceView` rich
  text block in the core registry; a note stores it as opaque JSON; if Workflow is absent the block
  renders as an "unavailable" placeholder. Activating Workflow *later* upgrades every existing note
  containing such blocks — activation order never matters.

### 3. Form (`gws_form`)

Structured data collection: forms, templates, external submissions.

| Entry point | Requires | Notes |
|---|---|---|
| "Create a data-collection form" | — | |
| "Collect data from external contributors" | — | share a form outside the workspace |
| "Embed a form in a note" | `note` (soft) | surfaces via Note's UI when both active |

- Bricks: `gws_form`. Dependencies: `enhanced_by: [note, workflow]` (form blocks in notes; a
  submission triggering a scenario is a candidate future cross-feature — see split plan point 15).

### 4. Project (`gws_project`)

Client/project workspaces: a document space per project, shared with external clients. It exists
today as an independent brick with its **own document table and its own filestore** — the living
proof that an app can be fully autonomous from the resource system.

| Entry point | Requires | Notes |
|---|---|---|
| "Manage project documents" | — | |
| "Share a document space with a client" | — | external access, app-owned auth |
| "Analyze a project document in the lab" | `workflow` | promotes the document into a resource |

- Bricks: `gws_project`. Dependencies: none hard; `enhanced_by: [workflow, search]`.
- The "analyze" entry point maps to the **on-demand promotion** pattern (split plan point 7,
  option 1): the document stays app-owned; analyzing copies it into the resource system with a soft
  back-link. Without Workflow, Project is complete — that entry point simply doesn't exist.

### 5. Search (`gws_search`)

The RAG tool: build knowledge bases from documents, then ask questions in natural language with
sourced answers. Technically grounded in the embedded RAG stack (LlamaIndex + LanceDB + pluggable
chat providers) planned in `gws_ai_toolkit`.

| Entry point | Requires | Notes |
|---|---|---|
| "Ask questions about your documents" | — | chat over indexed content |
| "Build a knowledge base" | — | datasets from uploaded files |
| "Index my lab resources / project documents / notes" | provider apps (soft) | see below |

- Bricks: `gws_search`. Dependencies: none hard; `enhanced_by:` *every app that publishes
  documents*.
- Search is the showcase of the **provider-registry pattern**, the N-way generalization of
  `enhanced_by`: Search defines a `DocumentSource` extension point (fetch a file, check staleness,
  enumerate candidates, open the original) and **never imports any other app**. Each app registers
  its own provider at load time: Workflow contributes "lab resources", Project contributes "project
  documents", Note contributes "notes". Activating any of them makes a new source appear in
  Search's dataset UI — with zero change to Search. Every document is snapshotted at add time, so
  retrieval keeps working even if the source app is later deactivated (graceful degradation again).

### What the catalog demonstrates

| Shape | Example |
|---|---|
| Standalone app | Workflow, Project alone on a lab |
| Hard `requires` on an entry point | Note's "report from results" → Workflow |
| Soft `enhanced_by` | Form blocks in notes |
| N-way provider registry | Search's document sources fed by Workflow, Project, Note |
| Order-independence | activate Note first, Workflow later — reports light up retroactively |

## Discovery

**One data model, several surfaces.** All discovery mechanisms below consume the same thing: the
**entry-point catalog** — the manifests' entry points ingested at publication into a queryable
store (`app, key, title, description, keywords, category, route, requires, locale`). At launch
scale (~10 apps × 3–5 entry points ≈ 50 rows) this is tiny, which dictates the technical choices.

### 1. The store (browse) — phase 1, required

A catalog page organized by **"what do you want to do"** — a small, manually curated
jobs-to-be-done taxonomy (5–7 categories: *Document & share*, *Analyze data*, *Collect data*,
*Find & ask*, …). Cards are **use cases, not apps**: "Create a report from analysis results" is a
card; the Note app is its subtitle. Clicking opens the app page (full description, screenshots,
all entry points, dependencies) with the Activate button. Cards carry the workspace state: `Active
→ Open` / `Activate` / `Installing…`.

### 2. Search — phase 1, near-zero cost

`GET /store/search?q=report` over `title + keywords + description`, plain weighted full-text SQL
(title > keywords > description). No search engine, no embeddings at this scale. The real work is
**editorial, not technical**: writing good need-phrased titles and generous keyword synonyms in
each locale — that's where "report" → Note is won or lost.

### 3. AI-assisted discovery — phase 3, optional, cheap

Reuses the planned lab AI agent ([ai_agent_chat_plan.md](ai_agent_chat_plan.md)) unchanged:

1. The user describes their need in natural language.
2. The agent has a `search_app_catalog(query)` tool — the same search endpoint as §2. (At ~50
   entries the whole catalog can even be injected into the system prompt: zero retrieval infra.)
3. The agent is grounded: it only recommends catalog results, never invents apps.
4. It disambiguates conversationally ("Write a note from scratch, or generate a report from an
   existing analysis?").
5. Its answer embeds a structured event rendered as an **action card** (entry point + Activate /
   Open button). The agent proposes; activation always goes through the orchestrator with explicit
   user confirmation.

### 4. The launcher — required, ships with activation

The post-activation surface, and the **boundary of this document's scope**: a "New…" menu in the
workspace built by crossing the entry-point catalog with the workspace's active capabilities. Each
item deep-links to its declared `route`. Entry points whose `requires` are unmet are hidden (or
shown as one-click upsells — to settle). The user never "navigates into an app"; they pick an
intent. Later refinement (out of scope now): contextual entry points (`context: scenario-result` →
"Create a report from this result" in a result's menu).

### Summary

| Surface | Status | Real cost |
|---|---|---|
| Entry-point catalog + ingestion at publication | **Foundation, required** | The actual work |
| Store browse | Required, phase 1 | One page + 2 endpoints |
| Full-text search | Required, phase 1 | Trivial (SQL over ~50 rows) |
| Launcher | Required, ships with activation | Front + capabilities crossing |
| AI discovery agent | Optional, phase 3 | Low (reuses search + planned chat) |

Nothing built in phase 1 is thrown away: all four surfaces read the same table.

## Activation — one verb, an orchestrator behind it

### User experience

One button: **Activate**. Then a progress state ("Installing… ~2 min"), then the app is `Active`
and its entry points appear in the launcher. Per-app states: `not active` / `installing` /
`active` / `update available` / `error` (with retry). That is the *entire* user-visible surface.

### What activation triggers

An **activation orchestrator** (living in the user-facing platform's backend) executes, per
activation request:

```
Activate(app, workspace)
  1. Resolve the manifest        → bricks + pinned versions, requires, core version
  2. Resolve dependencies        → unmet `requires`? propose co-activation or abort
  3. Resolve the runtime         → pick the target datalab; provision one if the
                                   workspace has none (placement policy — see below)
  4. Install                     → install brick(s) at pinned versions into the target lab,
                                   run the brick's own migration chain, reload
  5. Register                    → the lab's capabilities endpoint now reports the app;
                                   the app's load-time registrations (rich text blocks,
                                   taggable types, navigation, document sources…) are live
  6. Surface                     → workspace capabilities refresh; entry points appear in
                                   the launcher and the store card flips to Active
```

Steps 4–5 are exactly what the modular split makes cheap and safe: each brick owns its tables and
its `@brick_migration` chain, with **no cross-brick FK** — installing `gws_note` into a running
lab touches nothing else.

### Datalab topology is an implementation detail — the central architectural principle

**The deployment topology must never impact the user experience.** Whether a workspace is backed
by one datalab or several, the user sees one workspace, one store, one launcher, one activation
verb. Consequences, in decreasing order of certainty:

1. **The orchestrator owns placement.** "Which datalab runs this app" is a scheduling decision
   inside step 3 — policy-driven (fill the existing lab, or create/choose another by isolation,
   sizing, region, tenancy…), never a user question. Candidate topologies the orchestrator must be
   able to express, without the rest of the system caring:
   - one modular-monolith datalab per workspace (all activated apps in it — the split plan's
     default target);
   - several datalabs per workspace (per app, or grouping related apps);
   - later, mutualized/shared runtimes for small workspaces.
2. **If a workspace spans several datalabs, the datalabs can communicate with each other.**
   Lab-to-lab exchange is an accepted premise (a lab-to-lab communication layer exists in the
   current platform to build on). What the multi-lab case adds on top of the split's intra-lab
   mechanisms:
   - **Workspace-level capabilities aggregation.** The launcher and the store must read *the union
     of the workspace's labs* — a workspace-level capabilities view over the per-lab endpoints, and
     the only capabilities consumer anything user-facing talks to.
   - **Entry-point routing.** A launcher deep link must resolve `(workspace, app, route)` → the lab
     actually hosting the app. A workspace-level router/naming service owns that mapping; routes in
     manifests stay lab-relative.
   - **Cross-app references cross labs.** The split already forces soft `(entity_type, entity_id)`
     references, registries and events — none of which assume shared tables. In a multi-lab
     workspace these mechanisms need a remote transport (reference resolution, event propagation,
     `EntityLink` lookups via lab-to-lab APIs). This is the real technical cost of multi-lab and
     the strongest argument for the *"one lab per workspace as long as possible"* default — but it
     is an orchestrator/scale concern, invisible to users either way.
3. **Design consequence for everything in this document:** every user-facing component (store,
   launcher, agent, activation states) binds to the **workspace**, never to a datalab. Datalab ids
   appear only inside the orchestrator and operator tooling.

### Dependencies at activation

- **Hard `requires`** (app- or entry-point-level): the orchestrator computes the closure and
  proposes it upfront — "*Create a report from results* also needs **Workflow**. Activate both?"
  One confirmation, one combined install.
- **Soft `enhanced_by` / providers**: nothing to resolve at activation. Features materialize
  through the core registries whenever both apps happen to be active, in any order. Activating
  Project after Search makes "project documents" appear as a Search source with no action on
  either side.

### Deactivation (sketch — full policy to settle)

The split's graceful degradation is what makes deactivation *thinkable*: content referencing the
removed app stays intact as opaque JSON and renders placeholders; reactivation restores it.
Deactivation = uninstall the brick, keep (or archive) its tables/data per retention policy, refresh
capabilities. Entry points vanish from the launcher; store card returns to `Activate`.

### Walkthroughs

**W1 — first activation, standalone app.** A new user wants to share meeting notes. They search
"share note" → the "Write and share a note" card → Note app page → Activate. The workspace has no
runtime yet: the orchestrator provisions a managed datalab (defaults, invisible), installs
`gws_note` + core, registers. Two minutes later "New note" is in the launcher. No datalab, no brick
was ever mentioned. Note runs *alone* — the à-la-carte matrix at work.

**W2 — dependency and retroactivity.** The same user later runs analyses and wants a client
report. The store shows "Create a report from analysis results — needs Workflow". One click
activates Workflow; the orchestrator installs `gws_workflow` into the workspace's runtime (same lab
or another — invisible either way). The entry point appears — and any existing note that already
contained (placeholder) view blocks starts rendering them.

**W3 — provider pattern, zero coordination.** An org has Search active for its SOPs. Someone
activates Project. At `gws_project` load time its `DocumentSource` provider registers in the core
registry; Search's "add documents" dialog now lists *Project documents* as a source. Neither app
was modified; neither imports the other; the user did nothing but activate.

## Points to settle

1. **Manifest format and location.** Technical half versioned with the brick (e.g. in/next to
   `settings.json`) vs a separate published object; editorial content (screenshots, copy,
   localized descriptions) probably lives store-side. Validation rules at publication (route
   exists, requires resolvable, locales complete). The publication channel itself is out of scope
   here.
2. **Unit of activation and roles.** Per workspace/organization (assumed here) — with
   admin-activates / member-requests? Activation has infra and billing consequences; who sees what.
3. **Placement policy.** The orchestrator's rules for choosing/creating datalabs (default:
   fill the workspace's lab; when to split); sizing defaults for auto-provisioned labs; whether
   cost surfaces to admins and how. Must remain invisible to end users by principle.
4. **Workspace-level capabilities & routing.** Exact contract of the aggregated capabilities view
   and of entry-point resolution across labs; caching/staleness (a lab mid-install, a lab down).
5. **Lab-to-lab mechanisms for split apps.** If/when a workspace spans labs: transport for
   registry lookups, event propagation and `EntityLink` resolution across labs; failure semantics
   (degrade like an absent app?).
6. **Entry-point taxonomy & localization.** The fixed category list (product-owned); locale
   strategy for titles/keywords (fr/en at minimum); who writes and maintains the editorial quality
   that search depends on.
7. **Unmet-requires UX in the launcher.** Hide entry points whose `requires` are unmet, or show
   them as one-click upsells ("needs Workflow — Activate")?
8. **Update policy.** Store-managed auto-updates (fits "hide the technical" best; leans on the
   split's migration discipline) vs pinned + "Update available" badge; maintenance windows;
   rollback.
9. **Deactivation & retention.** Exact semantics: uninstall vs disable; table/data retention and
   export; effect on cross-app links (`EntityLink` deletion policies apply?); reactivation
   guarantees.
10. **Expert mode.** Operators and existing power users still need the technical view (labs,
    bricks, versions, logs). Where it lives and who sees it — the concepts are hidden, not deleted.
11. **Generalizing the provider pattern.** Search's `DocumentSource` registry and the rich-text
    block registry are the same shape (core-owned extension point + per-app registration). Worth
    defining a single core convention for declaring extension points in manifests, so `enhanced_by`
    becomes machine-checkable rather than editorial.

## Suggested sequencing

Each phase is independently shippable; none requires the modular split to be *finished* — phase 1
works against existing labs and bricks:

1. **Phase 1 — catalog + store + one-click install onto an existing lab.** Entry-point catalog,
   store page with browse + search, orchestrator v0 (install a brick into the workspace's existing
   lab, refresh capabilities). Removes most of today's friction on its own.
2. **Phase 2 — invisible runtime.** Auto-provisioning of the first datalab; placement policy;
   workspace-level capabilities; launcher. The datalab disappears from the UX.
3. **Phase 3 — AI discovery.** The agent + catalog tool + action cards, on top of the same data.

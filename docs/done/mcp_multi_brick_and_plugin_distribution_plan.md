# Plan: multi-brick MCP registry, and the lab serving its own Claude Code plugin

Two changes that only make sense together:

1. **Any brick can contribute MCP tools** to the one server the lab already mounts at `/mcp/`,
   instead of each brick standing up its own endpoint.
2. **The lab distributes the Claude Code plugin itself**, over public HTTP routes, instead of the
   plugin being published to a GitHub marketplace.

The second exists because of the first. A plugin published from a repository describes a fixed
set of tools; the tool set a lab actually serves is a function of *which bricks are installed and
at which versions*. Two labs on the same `gws_core` expose different surfaces. Only the lab knows
its own surface, so only the lab can describe it accurately.

An earlier attempt published the plugin from `gws_core` to `Constellab/agent-plugins` through
GitHub Actions. That work was reverted; this plan replaces it. The public repository keeps the
`space` and `community` plugins (single global endpoints, where a repository *is* the right
channel) and gains a page explaining the per-lab command.

---

## Established facts

Verified in the code, referenced here so the implementation does not re-derive them.

| | |
|---|---|
| **F1** | Bricks are folders on disk (`BrickInfo.path`), with `<brick>/src` added to `sys.path` (`settings_loader.py`). Files outside `src` are readable at runtime. |
| **F2** | `BrickService.import_all_bricks_in_python` imports **every** `.py` under `<brick>/src/`, called from the settings loader — well before `mount_mcp_app`. A decorator anywhere in a brick's source runs at startup, and the registry is populated before the MCP server is built. |
| **F3** | On a module import error the brick's load **stops mid-way**, and `TypingManager.unregister_unresolvable_typings(brick_name)` drops the registrations orphaned by it. Direct precedent for the MCP registry. |
| **F4** | Lab identity: `LAB_ID` (env, stable, `"1"` in local env) and `LAB_NAME` (env, human, defaults to `"Lab"`). |
| **F5** | `uvicorn.run` runs single-process (no `workers`), so an in-memory cache of the generated archive is coherent. |
| **F6** | `FastMCP.add_tool` accepts `annotations: ToolAnnotations` (`title`, `readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`) and a free-form `meta: dict`. No custom field is needed to describe a tool's effects. |
| **F7** | There is no generic key/value settings table. `gws_lab_config` (`LabConfigModel`) is a *snapshot* of brick versions with its own `hash` field, used for scenario reproducibility — not a settings store, and not to be confused with the plugin fingerprint below. |
| **F8** | `Settings` carries a `data` dict persisted to a JSON file, with `save()` and `set_data(key, val)` — `secret_key` already lives there. This is the persistence used by this plan. |

Client requirement: **Claude Code ≥ 2.1.224** (`archive` plugin sources). Below that the install
fails with an explicit message; below 2.1.120 the whole marketplace refuses to load. The `renames`
field needs ≥ 2.1.193, which is lower, so it adds no second prerequisite.

---

## A. The multi-brick MCP registry

**One endpoint, one OAuth issuer, one login.** Two MCP servers would mean two dynamic client
registrations, two browser consent round-trips and two refreshing tokens, for bricks that already
share the lab's `secret_key` and `User`.

- **Registration is a decorator**, on the model of `ApiRegistry` (a class-level registry filled at
  brick import, consumed at startup). Its options **mirror `FastMCP.add_tool`** — `name`, `title`,
  `description`, `annotations`, `icons`, `meta`, `structured_output` — rather than inventing a
  parallel vocabulary.
- **Tool names are prefixed with the brick name**, always, by the registry
  (`gws_invest_list_campaigns`). A `name` that already starts with its own prefix is a startup
  error, not a silent double prefix. Rationale: tool names end up in users' permission rules; a
  collision discovered in production is paid for with a rename, which breaks those rules silently.
- **`meta` is merged**, with `brick` and `brick_version` as reserved keys — free traceability of
  where a tool came from (F6).
- **A brick that failed to import is dropped entirely.** Its tools may already have been
  registered before the failing module (F3), so the registry filters bricks in error, and *both*
  the MCP server and the plugin generator read that filtered view. Serving half a brick is the
  worst of the three possible states. Log `CRITICAL` on the brick, as `BrickLogService` already
  does.
- **No opt-in.** Every brick that declares tools is exposed. The hard switch stays
  `GWS_MCP_SERVER_ENABLED`.
- **`gws_core` is a contributor like any other brick** — its two DB tools move onto the registry,
  with no special path.

### What this removes

The server-wide "everything here is read-only" promise in `INSTRUCTIONS` becomes false the moment
a brick registers a mutating tool. It goes away. The property descends to the tool level, carried
by `readOnlyHint` and the tool's own description.

- **Authorization is each brick's job.** The token is a full, unscoped lab session; authentication
  is not authorization. Every brick tool checks the calling user's rights itself.
- **Annotations are not restated in prose.** The client already reads them; duplicating them in
  the server instructions creates two sources of truth that diverge the day a brick changes an
  annotation without touching the text.
- **Context budget is the real ceiling.** Every tool's schema and description sits in every
  session connected to the lab. There is no per-brick switch to trim it — keep descriptions tight.

---

## B. The lab serves the plugin

Two public routes, mounted in the same conditional block as `/mcp/` — when
`GWS_MCP_SERVER_ENABLED` is false, neither exists. A 404 on the marketplace is a legible failure;
an installed plugin that never connects is not.

| Route | Stability | Who sees it |
|---|---|---|
| `GET /plugins/marketplace.json` | **never changes** | the user, once |
| `GET /plugins/<plugin>-<version>.zip` | changes with every version | nobody — read from the manifest |

The user runs `/plugin marketplace add https://<lab api url>/plugins/marketplace.json` once. The
archive URL lives *inside* the generated manifest and carries the version, so it changes freely —
which is what stops a proxy or CDN from serving a stale zip under a new version.

- **The manifest is generated per request** from the lab's own URL, version and registry. No
  `userConfig`: the lab knows where it is, so the user cannot point it at the wrong host.
- **The archive is built once and cached in memory** (bytes + version), read by both routes. It is
  a few KB of JSON and markdown, and F5 makes a single process cache coherent.
- **Version mismatch on the archive route answers 404** with an explicit message ("this lab now
  serves X, run `/plugin marketplace update`"), for the race where a client holds a manifest from
  before an upgrade. Never serve the current archive under a URL announcing another version.
- **Archive layout**: Claude Code looks for `.claude-plugin/` at the top of the zip or inside a
  single top-level folder, no deeper.
- **The generated content is public.** Two consequences: the manifest carries the fingerprint, not
  the list of installed bricks and versions; and a brick's `claude-plugin/` folder is public
  content — no customer names, no internal hostnames.
- **No `sha256` pin.** The version is declared explicitly (below), so byte-level reproducibility of
  the zip is not needed. The pin can be added later without breaking clients.

Local development is unchanged and unaffected: `archive` sources require HTTPS, so a lab on
`http://localhost` cannot use this channel. A root `.claude-plugin/marketplace.json` pointing at
the checkout, registered under a `-dev` name, stays the way to develop the plugin.

---

## C. Identity: two names, one immutable

| | Derived from | Changes? |
|---|---|---|
| Marketplace `name` | `constellab-<slug(LAB_ID)[:8]>` | **never** |
| Plugin `name` | `slug(LAB_NAME)` | follows the lab's name |

A renamed **marketplace** has no migration path — every user would have to re-add it. A renamed
**plugin** migrates itself through `renames` in the manifest. So the volatile half is the half
that can migrate.

- **Anonymous labs get a suffix.** `LAB_NAME` defaults to `"Lab"` (F4), so two never-named labs
  would both produce the plugin `lab` — and therefore *identical* permission ids
  (`mcp__plugin_lab_constellab__db_query`) despite distinct marketplaces. When the slug is empty or
  equals `lab`, append the same id characters as the marketplace: `lab-3f7a9c2e`. A named lab keeps
  `mon-lab`.
- **The history of served names is persisted in `Settings`** (F8): on each generation, if the
  current name differs from the last one served, append it. The manifest emits `renames` from that
  list. A full list, not just the last name, so two successive renames still migrate.
- **A lab rename costs users three things `renames` does not cover**, and this is accepted:
  one `/plugin install` to fetch the archive under its new name, their permission rules for the
  old tool ids no longer matching (they are re-prompted, with no error), and a new sign-in, since
  OAuth credentials are held per server entry and that entry derives from the plugin name. Priced
  against the real client under [what a lab rename actually costs](#what-a-lab-rename-actually-costs-its-users);
  the lab's rename screen says all three.
- **Every name the lab has ever served stays public.** The history is emitted as `renames` in an
  unauthenticated manifest, for the life of the lab — dropping an entry would strand the installs
  still on it. A lab named after a customer or an unannounced project carries that name in its
  manifest long after being renamed away from it. Nothing mitigates this; the rename screen says
  it, so the choice is made by someone who knows.
- **Known degraded case**: if the settings file is lost (recreated volume), the history goes with
  it, no `renames` is emitted, and existing installs point at a plugin name the manifest no longer
  lists. The user reinstalls. Rare, and silent.

---

## D. Versioning: fingerprint of the generated content

`version` = `<gws_core version>+<short hash of the generated content>` — the manifest, every tool's
name, description and schema, and every skill file.

Hashing the *brick versions* instead would churn every lab's plugin on any brick release, even one
that touched no tool; and — decisively — it would not change on a lab rename, leaving clients
holding a plugin whose name the manifest no longer uses. Hashing the content covers both: the lab
name is part of the content (plugin name, display name, injected skill descriptions), so a rename
propagates through the normal update path with no special case.

The version is declared in **both** the marketplace entry and `plugin.json`, generated together
from the same value. In the marketplace entry it lets Claude Code detect an available update
without downloading the archive.

---

## E. Skills come from the bricks

A skill names the tools it drives. A tool renamed in a brick while its skill lives in `gws_core`
breaks nothing loudly — the model just calls a tool that does not exist. So a brick ships both:
its tools under `src/`, its skills under `<brick>/claude-plugin/skills/<name>/SKILL.md` at the
brick root (F1).

- The generator collects the skills of every non-errored contributing brick into the archive.
- **The lab name is injected into each skill's description** at generation. Two labs installed side
  by side otherwise expose two identically-described skills, and the description is what the model
  reads when choosing.
- `gws_core`'s existing `query-lab-db` skill is rewritten as the skill of *the DB tools*, with the
  read-only promise moved from the server to the tools.

---

## Work items

Section A (items 1, 2, 5) is **done** — issue #104. Section B/C/D (items 3, 4, 6, 7) is **done**
— issue #105, which carried section E (the bricks' skills) with it, since the archive could not be
assembled without deciding what goes in it. Issue #106 closed on that state: it verified each of
its criteria against the code and added the missing coverage of *whose* skills are collected — a
brick in error, a brick declaring no tool, two bricks shipping a skill of the same name, and a
skill edit moving the version.

1. ~~**`McpRegistry`** — registry + decorator, brick prefixing, `meta` merge, filtering of bricks
   in error. Modelled on `ApiRegistry`.~~ `src/gws_core/mcp/mcp_registry.py`.
2. ~~**`build_mcp_server` consumes the registry** instead of adding two tools inline; server
   `instructions` generated from the contributing bricks.~~ Moved out of `db_mcp.py` into
   `src/gws_core/mcp/mcp_server_builder.py`, which is now the only consumer of the registry.
3. ~~**Plugin generator** — manifest (identity, version, `renames`, MCP server URL) + deterministic
   archive assembly + in-memory cache.~~ `src/gws_core/mcp/plugin_generator.py`, with the skill
   collection in `plugin_skills.py`.
4. ~~**Distribution routes** — `marketplace.json` and the versioned archive, public, mounted only
   when MCP is enabled, 404 on version mismatch.~~ `src/gws_core/mcp/plugin_controller.py`,
   registered from `App.start_uvicorn_app`'s `is_mcp_server_enabled` block, beside `mount_mcp_app`.
5. ~~**`gws_core` as a contributor** — move `db_list` / `db_query` onto the registry with their
   annotations; write `query-lab-db`.~~ `claude-plugin/skills/query-lab-db/SKILL.md`.
6. ~~**Identity persistence** — name resolution, suffix rule, history in `Settings`.~~
   `src/gws_core/mcp/plugin_identity.py`.
7. ~~**Docs** — brick author guide (declare a tool, choose annotations, authorization is the
   brick's job): `docs/mcp_brick_tools.md`, extended with shipping a skill and the public-content
   rule.~~
8. ~~**The per-lab command, told to the user** — with the Claude Code ≥ 2.1.224 prerequisite next
   to it. Not a page on the public repository (see the deviation below) but a screen of the lab's
   own front-end, backed by `GET /core-api/claude-plugin`:
   `docs/todo/claude_plugin_frontend_spec.md`.~~
9. ~~**The rename, verified and told** — what a lab rename costs an install, measured against the
   real client, and the warning text that goes on the rename screen.~~ Issue #107. It cost no
   production code: the mechanism shipped whole with #105, and every claim it rested on held.
   Recorded below, handed over in `docs/todo/claude_plugin_frontend_spec.md` §3.4.

## Verified during implementation

- **Files outside `src` survive.** The worry was misplaced: `MANIFEST.in` governs a python
  *package*, and a brick is never consumed as one. `SettingsLoader.load_brick` reads bricks as
  folders under the user or system bricks folder — `settings.json` at the root, code under `src/`
  — and `BrickInfo.path` is that root. `repo_type: "pip"` only records the absence of a `.git`;
  the folder travels whole either way. So `<brick>/claude-plugin/` is readable at runtime and
  `MANIFEST.in` is untouched.
- **Both generated manifests are accepted by Claude Code 2.1.227** (`claude plugin validate`),
  including a `+`-suffixed version, an `archive` source and a `renames` map. The one rejection is
  the one the plan predicted: an archive URL that is not HTTPS, or that points at a loopback host
  — which is exactly why local development keeps a checkout-backed marketplace.

## Deviations from the plan

- **The per-lab command is told to the user by the lab, not by the public repository.** The
  plan gave the public repo a page explaining the command; a generic page can only ever say
  "replace `<your lab>` with…", because the marketplace name comes from the lab's id, the
  plugin name from its name, and the version from the content it serves. So the lab states
  its own commands, on its own screen: `GET /core-api/claude-plugin` returns them ready to
  copy, plus the reason when the lab serves no plugin at all (MCP off, or a non-HTTPS URL).
  The front-end never rebuilds a command, so the naming rules keep one implementation. The
  public repository still needs a line pointing at that screen — it is the natural place to
  look first — but it is no longer where the instructions live.
- **The manifest is cached with the archive, not generated per request** (B said per
  request). The two must describe the same content, and nothing the generation reads can
  change while the process runs — the lab's URL, id and name come from the environment,
  and the registry is complete once the bricks are imported. Regenerating the manifest
  alone would only add a way for it to disagree with the cached archive. The cost is that
  changing `LAB_NAME` needs a restart, which is already true of every other consumer of
  that variable.

## What a lab rename actually costs its users

Issue #107. Measured against Claude Code **2.1.227**, driving the real client through
`claude plugin` with an isolated `CLAUDE_CONFIG_DIR`, against a marketplace carrying the map this
generator emits. What could not be measured that way is marked as such.

| | |
|---|---|
| **The `renames` map is followed, and one hop is enough** | A plugin installed as `mon-lab`, with the marketplace then renaming twice (`renames` = `{mon-lab: leur-lab, notre-lab: leur-lab}`), migrated straight to `leur-lab`. The flat map this generator emits — *every* former name pointing at the current one — needs no chain walking. |
| **The migration is a settings rewrite, and it happens on the next load** | `/plugin marketplace update` alone leaves `enabledPlugins` untouched. The next time Claude Code loads plugins it rewrites the key (`mon-lab@… → leur-lab@…`) in the user, project and local scopes, and prints `Renamed to "leur-lab" in the "constellab-…" marketplace` once. No user action beyond the update and the restart they were doing anyway. |
| **The MCP server entry is renamed with the plugin** | It is keyed `plugin:<plugin name>:<server key>`: `plugin:mon-lab:constellab` became `plugin:leur-lab:constellab`. |
| **So yes — users sign in again** | Credentials are held per server entry (`claude mcp login <name>` takes that id), and the rename gives the entry a new id, leaving the new one with none. Directly observed: the id changes. Not observed: the credential lookup missing, which needs a live OAuth round-trip against an HTTPS lab. |
| **And their permission rules stop matching** | Tool ids are `mcp__plugin_<plugin name>_<server key>__<tool>`, so every rule a user wrote names the old plugin. They are re-prompted, with no error. |
| **One `/plugin install` is needed on top of the update** | Plugin content is cached at `plugins/cache/<marketplace>/<plugin>/<version>`; after the rename nothing sits under the new name. A `directory` source is re-read from its path, but a remote one — `archive`, which is what this lab serves — reports `plugin-cache-miss`, and the docs are explicit that the user runs `/plugin install` once to fetch it under the new name. Not reproduced locally: an `archive` source needs a public HTTPS host, which is the same reason local development uses a checkout-backed marketplace. |
| **A lab renamed back to a former name is safe** | That name is both in the history and the current one. It is emitted as the rename *target* and never as a key, so the map cannot close a cycle — which `claude plugin validate` rejects outright, and a marketplace it rejects is one nobody can update. |
| **Managed and policy settings are not rewritten** | They are read-only to Claude Code. The plugin still loads, but the rename notice recurs at every start until an administrator updates `enabledPlugins` there. Affects labs whose plugin is deployed by policy, not individual users. |

So the honest account, and what the rename screen says: the install follows the rename by itself,
but the user runs `/plugin install` once, approves the renamed tools again, and signs in again.
The text handed to the front-end is in `docs/todo/claude_plugin_frontend_spec.md`.

### When the history is lost

The served names live in the `Settings` JSON file (F8). If that file goes — a recreated volume, a
lab rebuilt from scratch — the history goes with it. The lab then serves a manifest with no
`renames` for the names it served before, and an install pointing at one of them resolves to
nothing — `plugin-not-found`, per the documented behaviour for a name absent from both `plugins`
and `renames`; not reproduced here, for the same reason as the row above. Those users reinstall
from the same marketplace URL, which is unchanged. Nothing detects this, and nothing repairs it: the lab cannot know
a name it no longer remembers serving. It is the same degraded state as a save that fails, which
is why `_record_served_plugin_name` logs rather than raises — the manifest served *now* is correct
either way.

## Out of scope

- The lab front-end screen for renaming a lab — handled elsewhere; this plan only consumes
  `LAB_NAME`.
- Publishing a lab plugin to GitHub. Two channels for one plugin means two installable plugins
  declaring the same MCP server: duplicated tools and two logins.
- Scoped tokens. The token stays a full lab session; bricks check rights themselves. Worth
  revisiting once a brick ships a genuinely destructive tool.

# Frontend spec — "Connect Claude Code to this lab"

Status: draft · Backend: **implemented** (`GET /core-api/claude-plugin`, `PluginService`,
`gws_core/mcp/plugin_*.py`). Target: the Angular lab front-end.

---

## 1. What this screen is for

The lab serves its own Claude Code plugin: a marketplace manifest at a URL that never
changes, and the archive it points at. A user who wants Claude Code connected to their lab
needs three things — the marketplace URL, the plugin's name, and the minimum Claude Code
version — and none of them are guessable, because they are derived from the lab's id and
name.

So this screen is one thing: **the commands to copy, in the right order.** It is not a
settings screen; nothing on it is editable.

Where it goes is the front-end's call. It reads naturally as a section of the lab's
settings/about area, next to whatever already shows the lab's name and version.

**Why the lab and not a documentation page:** the tool surface depends on which bricks are
installed and at which versions, so two labs give two different plugins with two different
names. A generic page could only say "replace `<your lab>` with…"; this screen says the
actual command.

---

## 2. The endpoint

### `GET /core-api/claude-plugin`

Standard user auth header, like the rest of `/core-api` (no admin right needed — any lab
user may install the plugin). No parameters. Cheap and idempotent: call it when the screen
opens, no polling.

Response — `ClaudePluginInfoDTO`:

| field | type | present |
|---|---|---|
| `status` | `"AVAILABLE"` \| `"MCP_DISABLED"` \| `"URL_NOT_SUPPORTED"` | always |
| `lab_name` | `string` — the lab's human name | always |
| `minimum_claude_code_version` | `string`, e.g. `"2.1.224"` | always |
| `marketplace_name` | `string` | `AVAILABLE` only |
| `marketplace_url` | `string` — the URL added once | `AVAILABLE` only |
| `plugin_name` | `string` — the installable name (a slug) | `AVAILABLE` only |
| `version` | `string`, e.g. `"0.23.10+9c1707bd"` | `AVAILABLE` only |
| `mcp_url` | `string` — the endpoint the plugin connects to | `AVAILABLE` only |
| `commands` | object, see below | `AVAILABLE` only |

`commands`, all four ready to be copied verbatim — **do not build these client-side**, the
naming rules (slug, id suffix, rename history) live in the lab only:

| field | example |
|---|---|
| `add_marketplace` | `/plugin marketplace add https://glab.my-lab.constellab.io/plugins/marketplace.json` |
| `install` | `/plugin install mon-lab@constellab-3f7a9c2e` |
| `update_marketplace` | `/plugin marketplace update constellab-3f7a9c2e` |
| `update_plugin` | `/plugin update mon-lab` |

Example, `AVAILABLE`:

```json
{
  "status": "AVAILABLE",
  "lab_name": "Mon Lab",
  "minimum_claude_code_version": "2.1.224",
  "marketplace_name": "constellab-3f7a9c2e",
  "marketplace_url": "https://glab.my-lab.constellab.io/plugins/marketplace.json",
  "plugin_name": "mon-lab",
  "version": "0.23.10+9c1707bd",
  "mcp_url": "https://glab.my-lab.constellab.io/mcp",
  "commands": {
    "add_marketplace": "/plugin marketplace add https://glab.my-lab.constellab.io/plugins/marketplace.json",
    "install": "/plugin install mon-lab@constellab-3f7a9c2e",
    "update_marketplace": "/plugin marketplace update constellab-3f7a9c2e",
    "update_plugin": "/plugin update mon-lab"
  }
}
```

Example, not available:

```json
{
  "status": "MCP_DISABLED",
  "lab_name": "Mon Lab",
  "minimum_claude_code_version": "2.1.224"
}
```

---

## 3. The screen, per status

### 3.1 `AVAILABLE`

**Heading:** Connect Claude Code to this lab

**Lead:** Claude Code can use this lab's tools directly — read its databases, and whatever
else the installed bricks expose. Install the plugin this lab serves.

**Prerequisite, stated before the commands, not in a footnote:**

> Requires **Claude Code {{minimum_claude_code_version}} or later**. Check with
> `claude --version`, and run `claude update` if it is older.

**Step 1 — add this lab's marketplace.** Copy `commands.add_marketplace` into Claude Code.
Add: you only ever do this once; the address never changes.

**Step 2 — install the plugin.** Copy `commands.install`. Add: or run `/plugin` and pick
**{{plugin_name}}** from the list.

**Step 3 — restart and sign in.** Restart Claude Code when it asks, then run `/mcp` and
approve the access in the browser window that opens. The tools appear once you have.

**Details block** (secondary, collapsed is fine):

- Plugin `{{plugin_name}}`, version `{{version}}`
- Marketplace `{{marketplace_name}}`
- MCP endpoint `{{mcp_url}}`
- "The version moves whenever this lab's tools or skills change. To pull an update:
  `{{commands.update_marketplace}}` then `{{commands.update_plugin}}`."
- "If a download answers 404, your copy of the marketplace is older than the lab: run those
  two commands and install again."

**Rename warning** — this lives on the rename screen, not here. See §4.

### 3.2 `MCP_DISABLED`

No commands, no copy buttons.

> **Claude Code cannot connect to this lab.** Its MCP server is turned off, so there is
> nothing to connect to and no plugin to install. A lab administrator can enable it.

### 3.3 `URL_NOT_SUPPORTED`

No commands, no copy buttons.

> **This lab cannot hand out a plugin.** Claude Code only installs plugins from an
> `https://` address that is not a local one, and this lab is reachable at
> `{{mcp_url or the lab URL}}`. This is normal on a local development lab — register a
> local marketplace pointing at your checkout instead.

(The front-end does not need to detect this itself: the lab reports it.)

---

## 4. The rename screen

Not the screen above: wherever a lab administrator edits the lab's **name**. The plugin's name is
derived from it, so renaming the lab renames the plugin, and every user who installed it
pays something for that. They are never left broken — the lab's manifest carries the
migration — but three of the four things below are visible to them, so the administrator
has to know before they hit save.

Show it as a warning next to the name field, or in the confirmation dialog. It is the same
text whether or not the lab currently serves a plugin (`status` does not gate it): a lab
with its MCP server off may have served one before, and the installs are still out there.

**Heading:** Renaming this lab renames its Claude Code plugin

> Users who installed this lab's plugin keep it — the lab tells Claude Code about the new
> name, and every installation follows it, including ones made before an earlier rename.
> But each user has to do three things once, the next time they use it:
>
> - run `/plugin marketplace update` and then `/plugin install`, to fetch the plugin under
>   its new name;
> - approve its tools again, because permission rules mention the old name;
> - sign in again through `/mcp`.
>
> Nothing is lost and nothing breaks in the meantime. If you can, tell your users before
> renaming.

**Copy notes for whoever implements this:**

- **Don't soften it to "automatic".** The settings migration is automatic; the re-fetch, the
  permission prompts and the sign-in are not. A user promised a seamless rename will read
  the sign-in prompt as a failure.
- **Don't name the plugin's new name in the warning.** It is derived by the lab from the
  name being typed, and the screen would have to recompute the slug rules to show it —
  which §5 forbids. The new name appears on the "Connect Claude Code" screen after the
  rename takes effect.
- **The commands stay bare.** `/plugin marketplace update` and `/plugin install` without
  arguments are what the user types into Claude Code's own picker; the argument forms live
  on the "Connect Claude Code" screen, in `commands`, where they can be copied.
- **A rename takes effect when the lab restarts**, like every other consumer of the lab's
  name. Until then the lab keeps serving the plugin under the old name — so the
  "Connect Claude Code" screen still shows the old one, and that is correct, not stale.

**What the lab handles on its own, and the front-end does not mention:**

- Two or more renames in a row. The lab remembers every name it has served, so an install
  made before the first rename still migrates, in one step.
- Renaming back to a previous name. It resolves to a plugin that exists, with no loop.

**One more line, for a lab whose name is not public knowledge.** The migration works by the
lab publishing "this name is now that name" in a manifest served to anyone who knows the
lab's URL, and it must keep publishing it for as long as an install might still carry the
old name — which is forever. Worth saying on the screen where a lab named after a customer
or an unannounced project is renamed:

> The old name stays visible in the plugin this lab publishes, so that existing
> installations can find their way to the new one.

---

## 5. Behaviour notes

- **Every command gets a copy button.** They are typed into Claude Code, so copying is the
  whole interaction. Display them as code, in one line, without a leading `$`.
- **Never rebuild a command client-side**, not even by concatenating `marketplace_url`.
  `commands` exists precisely so the naming rules have one implementation.
- **Treat `version` as opaque.** It is `<gws_core version>+<fingerprint>` and it is not a
  semver to compare — the front-end displays it, nothing more.
- **Unknown `status` values** must render as the `MCP_DISABLED` case rather than crash: the
  enum can gain members.
- **No polling and no refresh button.** The values only change when the lab restarts.
- **Errors**: a failed call shows the standard error state; there is nothing to retry
  automatically.

---

## 6. Out of scope

- Anything that *changes* the plugin. There is no setting here — the marketplace name comes
  from the lab id, the plugin name from the lab name, the version from the served content.
- Enabling or disabling the MCP server (`GWS_MCP_SERVER_ENABLED`, set outside the lab).
- Listing the tools the plugin exposes. That list is what a client sees after connecting,
  and the manifest deliberately does not publish it.

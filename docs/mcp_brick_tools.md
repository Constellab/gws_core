# Declaring MCP tools from a brick

A lab mounts **one** MCP server, at `https://<lab api url>/mcp`. Any brick can add tools to
it; no brick stands up a server of its own. An MCP client (Claude Code, for instance) adds
the lab once, logs in once, and sees the tools of every installed brick.

The tool set is therefore a property of *the lab*, not of `gws_core`: two labs on the same
`gws_core` version expose different tools, because they have different bricks installed.

## Declare a tool

```python
from gws_core import McpRegistry
from mcp.types import ToolAnnotations


@McpRegistry.register_tool(
    "list_campaigns",
    title="List investment campaigns",
    description=(
        "List this lab's investment campaigns, most recent first.\n\n"
        "Args:\n"
        "  status: Filter on a campaign status, e.g. 'OPEN'. Omit for all.\n\n"
        "Returns a list of objects with 'id', 'name', 'status' and 'total_paid'."
    ),
    annotations=ToolAnnotations(readOnlyHint=True),
)
def list_campaigns(status: str | None = None) -> list[dict]:
    """The docstring and the type hints become the tool's schema."""
    ...
```

Put it anywhere under your brick's `src/`. Every module of every brick is imported at
startup, so the declaration is picked up wherever it lives — next to the service it calls is
usually the right place.

One exception: the brick importer skips modules and folders whose name starts with `_` (that
is how app code is kept off the startup path). A declaration in `_tools.py`, or under
`_internal/`, is never imported, so the tool simply never exists and nothing is logged.

The decorator returns the function unchanged: it stays an ordinary function, callable and
unit-testable without any MCP machinery.

Its parameters are exactly those of the MCP SDK's `FastMCP.add_tool` — `name`, `title`,
`description`, `annotations`, `icons`, `meta`, `structured_output`. There is no second
vocabulary to learn: whatever the SDK can express about a tool, you can express here.

## Names carry your brick's name

The registry prefixes every tool with the declaring brick, so `list_campaigns` declared by
`gws_invest` is served as `gws_invest_list_campaigns`.

Do not write the prefix yourself — declaring `gws_invest_list_campaigns` is a startup error,
not a silent `gws_invest_gws_invest_list_campaigns`.

The prefix is not decoration. A served tool name ends up in users' Claude Code permission
rules (`mcp__…__gws_invest_list_campaigns`). Renaming a tool because two bricks collided
would silently stop those rules from matching, so collisions are made impossible up front
and the remaining ones fail loudly at startup, naming both bricks.

## Choose the annotations

The server makes **no** promise about what its tools do — it serves whatever the installed
bricks declare. Each tool states its own effects, through its annotations:

| | |
|---|---|
| `readOnlyHint=True` | The tool only reads. Set it on every read tool: clients use it to decide what to run without asking the user. |
| `destructiveHint` | Only meaningful when the tool is not read-only. `True` for a tool whose effect cannot be undone. |
| `idempotentHint=True` | Calling it twice with the same arguments is the same as calling it once. |
| `openWorldHint=False` | The tool touches only the lab. `True` if it reaches an external service. |

They are hints, not enforcement: nothing stops a tool annotated `readOnlyHint=True` from
writing. Keeping them true is the brick's job, and a client that trusted the annotation will
not ask the user first.

## Your tool checks the caller's rights

The token an MCP client holds is a **full, unscoped lab session** — the same JWT the lab's
own routes accept. Authentication is not authorization: by the time your function runs, the
caller is a known lab user and nothing more has been decided.

So a tool that exposes anything not every lab user may see checks that itself, the same way
the brick's HTTP routes do:

```python
@McpRegistry.register_tool("list_investors", annotations=ToolAnnotations(readOnlyHint=True))
def list_investors() -> list[dict]:
    # CurrentUserService is populated by the transport, as on any lab route.
    CurrentUserService.check_is_admin()
    ...
```

`gws_core`'s own `db_list` / `db_query` need no such check, because read-only SQL over the
lab's databases is what any lab user can already do through the `gws db` CLI. That is a
property of those two tools, not a precedent.

## Keep descriptions tight

Every tool's name, description and schema sits in **every** session connected to the lab,
before the user has asked anything. There is no per-brick switch for a client to trim it.
Context budget is the real ceiling on how many tools a lab can usefully serve, so describe
what the tool does and what it returns, and stop there.

## Ship a skill with your tools

A skill is a markdown file telling the model how to drive your tools — which one to call
first, what the arguments mean, what a returned shape is good for. Ship it from **your**
brick, not from `gws_core`: a skill naming a tool you renamed while it lived somewhere
else breaks nothing loudly, it just tells the model to call something that does not exist.

Put it at your brick's root, outside `src/`:

```
gws_invest/
├── claude-plugin/
│   └── skills/
│       └── track-campaigns/
│           └── SKILL.md
├── settings.json
└── src/
```

The lab collects the skills of every brick that declares an MCP tool into the plugin it
serves (see below), one sub-folder per brick — so two bricks may ship a skill folder of
the same name.

Two rules for the file:

- **Front matter with a single-line `description`.** The lab rewrites that description to
  name the lab, so a user with two labs installed can tell the two copies apart. A
  description written as a YAML block (`|` or `>`) is left alone, with a warning in the
  lab's logs, and both labs then describe the skill identically.
- **Nothing private in it.** The plugin is served over an unauthenticated route to anyone
  who knows the lab's URL. A skill is documentation: no customer names, no internal
  hostnames, no credentials, no example data you would not publish.

## The lab hands out the plugin itself

The lab serves a Claude Code marketplace at `https://<lab api url>/plugins/marketplace.json`,
declaring one plugin: itself. A user adds that URL once and gets this lab's MCP server
plus the skills of its bricks. The lab's front-end shows them the exact commands, read from
`GET /core-api/claude-plugin`.

Nothing to do on your side beyond the two sections above — declaring a tool and, if it
helps, shipping a skill. The plugin's version is a fingerprint of what the lab serves, so
adding a tool, changing its description or its arguments, or editing a skill is enough for
installed clients to see an update.

The whole thing hangs off `GWS_MCP_SERVER_ENABLED`: with the MCP server off, the
marketplace route does not exist either.

## Metadata

`meta` is free-form and reaches the client as the tool's `_meta`. The registry adds two
reserved keys to it, `brick` and `brick_version`, so every served tool says where it came
from. Your own keys are kept alongside them.

## Failure modes

- **A brick that does not load completely serves none of its tools.** Modules are imported in
  order, so a brick whose import fails part-way may already have declared some tools. The
  registry drops all of them and the failure is logged as `CRITICAL` against that brick.
  Serving half a brick would show a client a tool set no version of the brick ever had.
- **A bad declaration stops your brick's load.** An already-prefixed name, or a name another
  brick already serves, raises while your brick is being imported — which means the rest of
  your brick does not load either. The message names the brick and the tool.
- **No MCP server, no tools.** The whole endpoint hangs off `GWS_MCP_SERVER_ENABLED`. When it
  is off, the declarations are still collected and simply never served.

## Where the code is

| | |
|---|---|
| `gws_core/mcp/mcp_registry.py` | the registry and the decorator |
| `gws_core/mcp/mcp_server_builder.py` | builds the server from the registry |
| `gws_core/mcp/mcp_controller.py` | mounts it, with the OAuth discovery routes |
| `gws_core/mcp/db_mcp.py` | `gws_core`'s own two tools, as a worked example |
| `gws_core/mcp/plugin_generator.py` | generates the marketplace manifest and the archive |
| `gws_core/mcp/plugin_identity.py` | the marketplace and plugin names, and renames |
| `gws_core/mcp/plugin_skills.py` | collects the bricks' skills into the archive |
| `gws_core/mcp/plugin_controller.py` | the two public routes, and the lab front-end's |
| `gws_core/mcp/plugin_service.py` | what the lab tells its own front-end |
| `gws_core/claude-plugin/skills/query-lab-db/` | `gws_core`'s own skill, as a worked example |

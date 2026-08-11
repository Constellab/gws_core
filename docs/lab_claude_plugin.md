# Connect Claude Code to your Constellab lab

> This page is the source for the equivalent page of the public
> [`Constellab/agent-plugins`](https://github.com/Constellab/agent-plugins) repository.
> Keep the two in step: the repository is where users look first.

Your lab hands out its own Claude Code plugin. There is no plugin to find in a
repository, and no URL to copy into a settings field beyond the one below — because the
tools a lab exposes depend on which bricks are installed in **that** lab, and only the
lab itself can describe them.

## Install it

Requires **Claude Code 2.1.224 or later** (`claude --version`; `claude update` if it is
older). Earlier versions cannot install a plugin distributed this way, and versions below
2.1.120 refuse to read the marketplace at all.

In Claude Code, replacing the host with your lab's API address:

```
/plugin marketplace add https://<your lab api url>/plugins/marketplace.json
/plugin install <your lab name>
```

`/plugin install` proposes the one plugin the marketplace declares — your lab. Restart
Claude Code when it asks, then run `/mcp` and log in: a browser opens on your lab, you
approve the access, and the tools appear.

You add the marketplace URL once. It never changes for the life of the lab.

## What you get

- **The MCP tools of every brick installed in your lab.** Each tool's name starts with the
  brick that declared it (`gws_core_db_query`, `gws_invest_list_campaigns`), so you can
  tell at a glance where a capability comes from.
- **The skills those bricks ship**, telling Claude how to use their tools.

Two labs therefore give you two different plugins, named after each lab. Installing both
side by side is normal and supported — each keeps its own name, its own login and its own
permission rules.

## Keeping it up to date

The plugin's version moves whenever the lab's surface does: a brick installed or upgraded
with a changed tool, a new skill, a lab renamed. To pull it:

```
/plugin marketplace update <your marketplace>
/plugin update <your lab name>
```

If a download ever answers **404**, the message tells you which version the lab serves
now: run the two commands above and install again. It means your marketplace copy is
older than the lab.

## If your lab is renamed

The plugin is named after the lab, so a rename changes the plugin's name. Claude Code
follows the rename by itself and migrates your installation. Two things it cannot carry
over:

- **your permission rules** for the old tool ids stop matching, so you are asked to
  approve those tools once more;
- **your MCP login**, which is stored per server entry, so you log in again through
  `/mcp`.

Nothing is lost, and no reinstall is needed.

## Troubleshooting

| | |
|---|---|
| `/plugin marketplace add` fails on the URL | The lab must be reachable over **HTTPS**. A lab served on `http://localhost` cannot distribute a plugin this way — use a local marketplace pointing at your checkout instead. |
| The marketplace URL answers 404 | The lab's MCP server is disabled. Ask the lab's administrator to enable it. |
| The tools do not appear after installing | Restart Claude Code, then run `/mcp` and log in. Tools appear only once the lab has authorized you. |
| A tool answers with a permission error | You are authenticated as your lab user, and nothing more: a tool may still refuse what your account may not do in the lab itself. |

## The other Constellab plugins

`space` and `community` are published from
[`Constellab/agent-plugins`](https://github.com/Constellab/agent-plugins) in the ordinary
way, because each talks to a single global endpoint that is the same for everyone. A lab
is the opposite case, which is why it distributes itself.

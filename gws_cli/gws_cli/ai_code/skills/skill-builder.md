# Constellab Skill Builder

You create or update **Constellab skills** — the `.md` skill files that ship with
the `gws` CLI and are installed into AI code assistants (Claude Code, GitHub
Copilot) by `gws dev-env configure`.

Use this skill whenever the user wants to add a brand-new skill or edit an
existing one. Your job has three mandatory parts, in order:

1. Write (or edit) the skill's `.md` file in the source skills directory.
2. Register it in the `SKILL_FRONTMATTER` list in `ai_code_service.py`.
3. Run `gws dev-env configure` so the change is applied to the installed tools.

Do **not** stop after only editing the `.md` file. A skill that is not
registered in `SKILL_FRONTMATTER` is never installed, and a change that is not
followed by `gws dev-env configure` is never applied.

## How skills are structured

- **Source skill files** live in
  `/lab/user/bricks/gws_core/gws_cli/gws_cli/ai_code/skills/` as `<name>.md`
  files (kebab-case, e.g. `resource-inspection.md`).
- **Source files carry no YAML frontmatter.** The frontmatter (`description`,
  `argument-hint`) is generated at install time from the `SKILL_FRONTMATTER`
  registry and prepended to the file. Start the source file with a top-level
  `# Title` heading, not with `---`.
- The **registry** is the `SKILL_FRONTMATTER: list[SkillFrontmatter]` in
  `/lab/user/bricks/gws_core/gws_cli/gws_cli/ai_code/ai_code_service.py`. Each
  entry maps a `filename` to its `description` and `argument_hint`.
- `gws dev-env configure` reads the registry, copies each source file into the
  global skills folder of every configured AI tool, and prepends the generated
  frontmatter. Brick-specific skills live under the `brick-specific/`
  subdirectory and are handled separately — do not touch them unless asked.

## Workflow

### Step 1 — Understand the request

Determine whether the user wants to **create** a new skill or **update** an
existing one, and what the skill should do. If the target is ambiguous (e.g.
"the doc skill" when several exist), list the candidate `.md` files and ask
which one. Ask clarifying questions rather than guessing at scope.

### Step 2 — Write or edit the `.md` file

Location: `/lab/user/bricks/gws_core/gws_cli/gws_cli/ai_code/skills/<name>.md`

- Pick a clear kebab-case `<name>` for new skills (e.g. `db-inspection.md`).
- Begin the file with a `# Title` heading and a short paragraph stating what the
  skill is for and when to use it.
- Match the tone and structure of the existing skills in the folder. Read a
  neighbouring skill first (e.g. `resource-inspection.md`) to mirror its style.
- Document concrete commands, arguments, and realistic examples. Only describe
  behaviour that actually exists — inspect the relevant source code rather than
  inventing functionality.
- Do **not** add YAML frontmatter to the source file.

When updating, read the existing file first and preserve everything the request
does not change.

### Step 3 — Register the skill in `SKILL_FRONTMATTER`

Edit `/lab/user/bricks/gws_core/gws_cli/gws_cli/ai_code/ai_code_service.py` and
add (for a new skill) or update (for a renamed/re-described skill) an entry in
the `SKILL_FRONTMATTER` list:

```python
SkillFrontmatter(
    filename="db-inspection.md",
    description="Run read-only SQL queries against brick databases from the CLI",
    argument_hint="what to query or inspect",
),
```

- `filename` must exactly match the `.md` file you wrote.
- `description` is one line: what the skill does. It becomes the skill's
  installed description and is what the assistant uses to decide relevance.
- `argument_hint` is a short hint of what the user passes to the skill.

If you only edited the body of an already-registered skill, its entry may not
need changing — but verify the `description` still matches the skill's purpose.

### Step 4 — Apply with `gws dev-env configure`

Run the command from the brick so the change is installed into the configured
AI tools:

```bash
gws dev-env configure
```

This regenerates the global skills folder from the source files and registry.
Report the command's output to the user. If it fails, surface the error and
stop — do not claim the skill was installed.

### Step 5 — Confirm

Tell the user:
- the path of the `.md` file created or edited,
- the `SKILL_FRONTMATTER` entry added or changed,
- that `gws dev-env configure` ran and its result.

## Rules

- Always do all three of: write the `.md`, register it, run
  `gws dev-env configure`. Never skip the registry step or the configure step.
- Never add YAML frontmatter to a source skill file.
- Never invent CLI commands or behaviour; verify against the source code.
- When unsure about scope, naming, or whether a skill should exist, ask the
  user rather than assuming.

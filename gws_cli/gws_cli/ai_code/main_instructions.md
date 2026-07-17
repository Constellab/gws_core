# AI Code Instructions

This file provides guidance to AI tools when working with code in this repository.

## Workspace Structure
```
/lab/user/
├── bricks/                # Directory containing all bricks (libraries)
├── data/                  # Data directory
└── notebooks/             # Jupyter notebooks
```

Each brick has its own `CLAUDE.md` for brick-specific guidance. 

## Development Commands


### Server Management
- Start server: `gws server run`
- Start server with debug logging: `gws server run --log-level=DEBUG`

### Testing
- **Run all tests**: `gws server test all`
- **Run specific test**: `gws server test [TEST_FILE_NAME]` (without `.py` extension, run from the brick directory)
- Tests are located in each brick's `tests/` directory
- Example: `cd bricks/gws_ai_toolkit && gws server test test_table_copilot`
- **Run tests in parallel**: add `--parallel` to run via pytest-xdist. Each worker gets its own test DB schema.
  - Example: `gws server test all --parallel`
  - Control the worker count with `--workers` / `-n` (default `auto`, one worker per CPU); only takes effect with `--parallel`.
  - Example: `gws server test all --parallel -n 4`

### Development Apps
- Run Streamlit app in dev mode: `gws streamlit run [CONFIG_FILE_PATH]`
- Run Reflex app in dev mode: `gws reflex run [CONFIG_FILE_PATH]`
- **When creating, modifying, or debugging any Reflex app code, FIRST invoke the `gws-reflex-app-developer` skill** to load the global Reflex rules.
- **When creating, modifying, or debugging any Streamlit app code, FIRST invoke the `gws-streamlit-app-developer` skill** for the equivalent Streamlit rules.

### Brick Management
- **Generate new brick**: `gws brick generate [NAME]`
- **Generate task class**: `gws task generate`
- **Install dependencies**: Dependencies are defined in each brick's `settings.json`

### Bump and Publish a Brick Version
Run from the brick folder (or pass its path as an argument):
1. **Bump the version manually** in the brick's `settings.json` (`"version"` field). Also bump the gws_core dependency if needed.
2. **Commit it**
3. **Publish**: `gws brick version push`
   - Options: `-y` to skip every prompt, `-td` to push the technical documentation at the same time
- **To push the technical documentation alone** (no new version): `gws brick technical-doc push`

### Database Queries (read-only)
- **Run a query**: `gws db query "SELECT ..." --db [BRICK_NAME]`
- `--db` defaults to `gws_core`; pass a brick name (e.g. `gws_invest`) to query its database
- **List databases**: `gws db list`
- Only read-only statements are allowed (SELECT/SHOW/EXPLAIN/DESCRIBE); writes are blocked
- Options: `--format json` for parseable output, `--limit N` to cap rows (default 20, `0` for no limit)
- Example: `gws db query "SHOW TABLES" --db gws_invest`

### Resource Inspection (read-only)
- Inspect lab resources from the CLI: `search` (find), `info` (metadata), `fields` (list RFields), `read` (read RField values, e.g. a DataFrame), `views` / `call-view`.
- Example: `gws resource search --filter '[{"key":"name","operator":"CONTAINS","value":"iris"}]'`
- **When searching for or inspecting resources, see the `resource-inspection` skill** for the operators, keys, and search defaults that hide rows.

### Scenario Inspection (inspect & control)
- Inspect scenarios from the CLI: `search` (find), `info` (metadata), `running`, `error` (failure info), `protocol` (process graph), `resources` (produced/consumed). `start` / `stop` change state and require `--yes`.
- Example: `gws scenario search --filter '[{"key":"status","operator":"EQ","value":"ERROR"}]'`
- **When searching for or inspecting scenarios, see the `scenario-inspection` skill** for the operators and keys.

### Constellab Chat Expert
- **Ask a question**: `gws community ask-chatbot "My question?"`
- This is a RAG-powered assistant that can answer:
  - Product questions about the Constellab platform (features, concepts, workflows)
  - Technical questions about developing on the platform (tasks, resources, protocols)
  - Questions about the gws_core library (classes, methods, patterns, best practices)
  - API usage, conventions, and coding guidelines
- Use this tool BEFORE writing code if you have any doubt about how something works on Constellab

### Developer FAQ
- The developer FAQ lives on the Community, under the **Developer guide** folder: one `FAQ` page per domain subfolder, plus a fallback `FAQ` page directly in `Developer guide`.
- **When you finish diagnosing a non-obvious error, offer to save it to the FAQ** — then invoke the `gws-faq` skill if the user accepts. Offer only when the cause is understood AND the fix is verified AND the error was hard to diagnose (the message did not point to the fix). Offer once, and drop it if the user declines.
- **When debugging an error, consider checking the FAQ first** — it may already be documented.

### Best Practices

#### General Rules
- When exploring (`ls`/`find`/`grep`/`cat`), run each as a separate single-tool Bash call instead of chaining them with `cd ... && ...`, `;`, or `|` into one compound command. Single-tool calls match the existing permission allowlist (so they don't prompt) and independent ones can run in parallel; compound chains fall through to a permission prompt. Prefer the dedicated Read/Grep/Glob tools where they fit.
- Always read files before editing them. Never assume file contents — use the Read tool first to understand current state
- Don't over-explore the codebase. When the task is clear (e.g., write documentation, create a file), start working immediately rather than reading unrelated files
- Follow existing coding conventions and styles. When implementing new features, look for similar existing implementations and match their approach (e.g., file storage patterns, SDK object usage, import styles)
- Write comprehensive docstrings for classes and methods
- Do not export classes in the __init__.py files unless necessary
- Always place import statements at the top of the file (module level). Never import inside functions, methods, or other non-top-level scopes
- Once modifications are finished, run `ruff check --fix` on the modified files and fix simple errors

#### Refactoring Rules
- When refactoring or restructuring files, verify all existing functionality is preserved. After moving/rewriting code, check that no functions, imports, or features were accidentally removed
- After large refactors, grep for references to functions from the original file to catch anything broken

#### UI/Styling Rules
- When asked to remove a color or style, remove the property entirely rather than replacing with another explicit value. Prefer framework defaults over explicit alternatives


# Scenario Inspection (`gws scenario`)

Commands to inspect and control lab scenarios from the CLI. Use them to find a
run, see if it succeeded, see what it produced, read its protocol, and (with
confirmation) start or stop it.

Most commands are read-only. **`start` and `stop` change scenario state and
require the `--yes` flag.**

Requires a reachable lab DB (start `gws server run` first if needed). Errors are
printed to stdout with a concrete next action.

## Commands

### `gws scenario search` — find scenarios

Uses the advanced, operator-based search. Pass criteria as a JSON list via
`--filter`:

```bash
gws scenario search --filter '[{"key":"status","operator":"EQ","value":"ERROR"}]'
```

Each criterion is `{"key": <field>, "operator": <OP>, "value": <val>}`
(`operator` defaults to `EQ`).

**Operators:** `EQ` `NEQ` `LT` `LE` `GT` `GE` `CONTAINS` `IN` `NOT_IN` `NULL`
`NOT_NULL` `START_WITH` `END_WITH` `MATCH` `BETWEEN`.

**Common keys:** `title`, `status` (`DRAFT` / `IN_QUEUE` / `RUNNING` /
`SUCCESS` / `ERROR` / `PARTIALLY_RUN`), `is_validated`, `is_archived`,
`created_at`, `folder`.

**Special keys:**
- `process_typing_name` — scenarios that contain a given task/process type.
- `tags` — value is a list of tag objects: `[{"key":"experiment","value":"x1"}]`.

**Other options:** `--sort '[{"key":"created_at","direction":"DESC"}]'`,
`--page N` (0-based), `--limit N` (per page), `--format json`.

### `gws scenario info <id>` — metadata

Prints the scenario's metadata as JSON (title, status, validated, archived,
folder, timestamps, embedded protocol).

### `gws scenario running` — list running scenarios

Lists the currently running scenarios with their per-task progress. No id
needed. Supports `--format json`.

### `gws scenario error <id>` — failure info

For a failed scenario, prints the error detail as JSON (message, unique code,
context). Reports "no error info" if the scenario did not error.

### `gws scenario protocol <id>` — protocol graph

Prints the scenario's protocol as JSON (the full process graph: nodes, links,
interfaces, outerfaces, layout). This can be large for complex scenarios.

### `gws scenario resources <id>` — produced/consumed resources

Lists the resources a scenario produced and consumed (id, name, type). Use the
ids with the `gws resource` commands to inspect their data. Supports
`--format json`.

### `gws scenario start <id> --yes` — start a scenario

Queues the scenario for execution. **Changes state** — refuses to run unless
`--yes` is passed.

### `gws scenario stop <id> --yes` — stop a scenario

Stops a running scenario. **Changes state** — refuses to run unless `--yes` is
passed.

## Typical flow

```bash
gws scenario search --filter '[{"key":"status","operator":"EQ","value":"ERROR"}]'
gws scenario info <id>
gws scenario error <id>
gws scenario resources <id>
```

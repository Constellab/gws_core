# Resource Inspection (`gws resource`)

Read-only commands to inspect lab resources from the CLI. Use them to find a
resource, see what it is, and read its data without writing any code. All
commands are read-only (they never mutate resources).

Requires a reachable lab DB (start `gws server run` first if needed). Errors are
printed to stdout with a concrete next action.

## Commands

### `gws resource search` — find resources

Uses the advanced, operator-based search. Pass criteria as a JSON list via
`--filter`:

```bash
gws resource search --filter '[{"key":"name","operator":"CONTAINS","value":"iris"}]'
```

Each criterion is `{"key": <field>, "operator": <OP>, "value": <val>}`
(`operator` defaults to `EQ`).

**Operators:** `EQ` `NEQ` `LT` `LE` `GT` `GE` `CONTAINS` `IN` `NOT_IN` `NULL`
`NOT_NULL` `START_WITH` `END_WITH` `MATCH` `BETWEEN`.

**Common keys:** `name`, `id`, `data`, `created_at`, `created_by`, `origin`,
`folder`, `is_archived`.

**Special keys:**
- `resource_typing_name` / `resource_typing_names` — match the type AND its subtypes (the second takes a list, use with `IN`).
- `generated_by_task` — filter by the task that produced the resource.
- `tags` — value is a list of tag objects: `[{"key":"experiment","value":"x1"}]`.
- `column_tags` — Table resources only.

**IMPORTANT defaults that hide rows:** by default only *flagged* resources are
returned and children are excluded. To widen the search, add:
- `{"key":"include_not_flagged","value":true}`
- `{"key":"include_children_resource","value":true}`

**Other options:** `--sort '[{"key":"created_at","direction":"DESC"}]'`
(default: `created_at DESC`), `--page N` (0-based), `--limit N` (per page),
`--format json`.

Example — first 5 Tables, including unflagged:

```bash
gws resource search --limit 5 --filter '[
  {"key":"resource_typing_names","operator":"IN","value":["RESOURCE.gws_core.Table"]},
  {"key":"include_not_flagged","value":true}
]'
```

### `gws resource info <id>` — metadata

Prints the resource's metadata as JSON (name, type, origin, scenario, folder,
flags, ...). Fast — does not load the resource content.

### `gws resource fields <id>` — list RFields

Lists the resource's RFields (its declared, persisted fields), each shown as
`name (RFieldType) -> ValueType`, e.g. `_data (DataFrameRField) -> DataFrame`.
These are the names you pass to `read`.

### `gws resource read <id> <rfield...>` — read RField values

Prints one or more RField values. The name must be an RField (otherwise the
error lists the valid ones). DataFrame/Series values are summarized with their
shape and a row-limited preview; `--limit N` caps the rows (default 50, `0` for
no limit).

```bash
gws resource read 5675b0cb-... _data --limit 10
```

### `gws resource views <id>` — list views

Lists the views available for the resource type (method name, human name, view
type, default marker).

### `gws resource call-view <id> <view_name>` — render a view

Renders a view as JSON. Pass view config values with `--config '{...}'`. Often
the most useful agent-facing summary of a resource. List names with `views`.

## Typical flow

```bash
gws resource search --filter '[{"key":"name","operator":"CONTAINS","value":"iris"}]'
gws resource info <id>
gws resource fields <id>
gws resource read <id> _data
```

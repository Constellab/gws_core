# Community doc CLI round-trip & `gws-update-doc-json` skill improvements

## Context

The `gws community` CLI ([community_cli.py](../../gws_cli/gws_cli/community_cli.py)) and the
`gws-update-doc-json` skill together let a developer edit Constellab Community documentation
pages (EditorJS / RichTextDTO content) from the workspace. In practice, editing a single
existing page — updating one glossary block on the "Getting started" page in the
`gws_academy` brick — was slow and error-prone. This plan records the friction points found
during that task and the improvements that would make the flow smooth.

The root causes are: (1) `get-doc` and `update-doc` do **not** exchange the same file format,
so the obvious get → edit → put loop is broken with no warning; and (2) the skill is written
entirely around a `doc_manifest.json` + brick-discovery flow, so a page that lives in a brick
not present in the workspace (and in no manifest) dead-ends the documented workflow even though
the CLI only ever needs the page's `remote_doc_id` — which is present in the page URL.

## What went wrong (observed)

1. **`get-doc` writes markdown, `update-doc` reads JSON.** `get_documentation` calls
   `rich_text.to_markdown(include_block_comments=True)` and writes markdown (with
   `<!-- blockId | type -->` comments). `update_documentation` does `json.load(f)` →
   `RichTextDTO.from_json(...)`. Feeding the `get-doc` output straight back into `update-doc`
   raises a raw `json.decoder.JSONDecodeError: Expecting value: line 1 column 1` — no hint
   that the file is markdown, not JSON. There is no `RichText.from_markdown`, so the markdown
   cannot be converted back either.

2. **Only workaround is a bespoke script.** To get the *raw* RichTextDTO JSON, one has to
   import the community service directly and call `result.content.to_json_dict()`. A naive
   `python3 -c '...'` fails with `ModuleNotFoundError: No module named 'gws_core'` because the
   CLI's `sys.path` bootstrapping is not applied; the script must prepend
   `/lab/user/bricks/gws_core/src` and the brick root manually.

3. **The skill assumes a manifest + local brick.** Step 1 discovers the brick under
   `/lab/user/bricks/` and stops if not found; Mode B reads `doc_manifest.json` and stops if
   the doc is not listed. A page in `gws_academy` (not in the workspace, not in any manifest)
   has no path through the skill, yet the CLI needs only the doc id — which is in the URL
   (`.../doc/getting-started/<doc_id>#brick`).

4. **`.json` naming lie.** The skill names the `get-doc` output `doc_current.json`, but the
   content is markdown. This is what leads a reader to try `json.load` on it first.

5. **No verify step.** Skill Step B7 ends at upload. A malformed block can be accepted and
   render as an empty page, so a re-fetch/diff after upload is worth making explicit.

## Improvements

### A. Make `get-doc` / `update-doc` round-trip (highest impact)

Add a format option to `get-doc` so the editable artifact can be canonical JSON:

```
gws community get-doc <id> <output_path> --format json|markdown   # default: json
```

- `--format json` writes `result.content.to_json_dict()` (RichTextDTO), which `update-doc`
  reads back unchanged. This removes the need for any side-script and makes the skill's
  get → edit → put loop work as written.
- `--format markdown` keeps today's human-readable output (with block-id comments) for
  reading/reviewing.
- **Default to `json`** so the round-trip is the happy path; markdown becomes opt-in.

Implementation sketch in [community_cli.py](../../gws_cli/gws_cli/community_cli.py)
`get_documentation`:
- add `output_format: Annotated[str, typer.Option("--format", ...)] = "json"`.
- `if output_format == "json": json.dump(RichText(result.content).to_dto_json_dict(), f, indent=2, ensure_ascii=False)`
  (or `result.content.to_json_dict()`); `else:` current markdown path.

**Caveat — markdown is lossy.** Markdown cannot represent every block type faithfully
(`hint` type, `table`, code `language`, exact block ids for unchanged blocks). Keep **JSON as
the canonical editable format**; never let a markdown file be the thing pushed back, or blocks
will silently drop on round-trip. (A real `RichText.from_markdown` is a larger, lossy effort —
out of scope; `--format json` sidesteps it entirely.)

### B. Fail `update-doc` with a helpful message on markdown input

Cheap safety net regardless of A: in `update_documentation`, wrap `json.load(f)` and, on
`JSONDecodeError`, detect the tell-tale `<!-- ... | ... -->` block comment or leading `#`
markdown heading and emit:

> `Error: <path> looks like markdown output from 'get-doc'. Re-fetch with 'get-doc <id> <path> --format json' before updating.`

instead of a raw stack trace.

### C. Add "Mode C — update by URL or doc id" to the skill

Skill file: `/home/labuser/.claude/skills/gws-update-doc-json/` (the skill markdown that
defines Modes A/B). Add a third mode at the top of the workflow that does **not** require a
brick or manifest:

- **Input:** a Community doc URL *or* a raw `remote_doc_id`. Parse the id out of
  `.../doc/<folder-slug>/<doc_id>#...` (the id is the last path segment before any `#`).
- **Flow:** `get-doc <id> ... --format json` → edit the target block(s) in the JSON
  (preserving block `id`s) → `update-doc <id> ...` → re-fetch to verify.
- Keep Modes A/B for the source-code-sync story, but make ad-hoc "just fix this one page" a
  first-class door. This is the change that turns the task from "read skill, dead-end, write
  bespoke script, debug import paths" into "paste URL → edit one line → push".

### D. Fix the format contract in the skill

- Rename the example output from `doc_current.json` to `doc_current.md` **or** (preferably,
  combined with A) make the output real JSON and keep `.json`.
- Add a short format-contract table near the top of the skill so the I/O formats are explicit:

  | Command      | Reads              | Writes                                  |
  | ------------ | ------------------ | --------------------------------------- |
  | `get-doc`    | —                  | JSON (default) / markdown (`--format`)  |
  | `update-doc` | RichTextDTO JSON   | —                                       |

### E. Make "verify after upload" an explicit skill step

Add a final step to Mode B (and Mode C): re-fetch the page and diff the changed block(s) to
confirm the update landed and did not produce an empty render. Cheap, and it catches
malformed-block-accepted-but-empty-page failures.

### F. (Optional, minor) Reduce fallback import friction

When a script fallback is still needed, the two `sys.path.insert` lines (`.../gws_core/src`
and the brick root) are the canonical "run a script in the gws env" recipe. Either document
that snippet in the skill's troubleshooting section, or expose a `gws` subcommand that runs an
arbitrary script with the environment already bootstrapped, so no manual path juggling is
required.

## Priority

1. **A** — `get-doc --format json` (unblocks the whole loop).
2. **C** — update-by-URL mode in the skill (removes the manifest dead-end).
3. **B, D, E** — polish: clear error, honest naming + format table, verify step.
4. **F** — optional convenience.

Together A + C turn single-page edits from a multi-step, script-and-debug ordeal into
"paste URL → edit block → push".

## Scope

- CLI changes: [community_cli.py](../../gws_cli/gws_cli/community_cli.py) (`get-doc`
  `--format`, `update-doc` error handling). No server/API changes required — the community
  service already returns RichTextDTO content.
- Skill changes: the `gws-update-doc-json` skill markdown (new Mode C, format table, naming
  fix, verify step).

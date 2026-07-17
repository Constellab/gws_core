# FAQ Entry Capture

You capture a **solved error** into the developer FAQ on the Constellab Community,
so the next developer who hits the same error finds the fix instead of
re-diagnosing it.

Use this skill when the user asks to save an error to the FAQ, or accepts your
offer to do so after a debugging session. The input is an error that has been
**diagnosed and fixed** — not an open problem.

## Prerequisites

Do not capture an entry until all of these hold. If any fails, say so and stop.

- **The error is understood.** You know the mechanism, not just the symptom.
- **The fix is verified.** It actually worked. A guess is worse than no entry,
  because a wrong FAQ entry sends the next reader down a dead end with false
  confidence.
- **The error is non-obvious.** Skip anything whose message already tells you the
  fix (a typo, a missing argument the traceback names). The FAQ is for errors
  where the message and the cause are far apart.

## Where FAQ pages live

FAQ pages live on the Community, under the **Developer guide** folder of the
`gws_core` documentation tree. There are two kinds:

- **Domain FAQ** — a page titled `FAQ` inside a direct subfolder of
  `Developer guide`. Each one covers errors in that subfolder's domain.
- **Fallback FAQ** — a page titled `FAQ` directly in `Developer guide`, for
  errors that are general or whose domain is unclear.

**Never hardcode the subfolder names or their IDs in this skill or anywhere
else.** The tree changes as documentation grows. Always read it live (Step 2)
and route against what you find.

FAQ pages are deliberately **not** tracked in `doc_manifest.json`. That manifest
links docs to `source_files` so they can be regenerated from code; FAQ entries
come from lived debugging, not from source, so they do not fit that model. Do
not add them to it.

## The `update-doc-json` skill owns the mechanics

FAQ pages are ordinary Community documentation pages stored as **EditorJS
JSON**. The `update-doc-json` skill is the reference for all of it — **read it
before you touch a page** and follow it for:

- the folder tree (`gws community doc-hierarchy`), and where `community_brick_id`
  comes from,
- fetching a page (`gws community get-doc`),
- creating a page (`gws community create-doc`) and a folder
  (`gws community create-folder`),
- uploading content (`gws community update-doc`),
- the EditorJS block types (`header`, `paragraph`, `code`, `list`, `table`,
  `hint`), their exact `data` fields, and the block ID rules.

Do not restate or re-derive those rules here. This skill only adds **what an FAQ
entry is, and which page it belongs on**.

The one rule worth repeating, because breaking it silently destroys other
people's work: when you update an existing page, **preserve the `id` of every
block you did not change**, and never drop a block you did not intend to touch.

## Workflow

### Step 1 — Draft the entry and confirm it

Before touching the Community, write the entry out and show it to the user.

An entry is one `##` section. Its parts:

- **Heading (`header`, level 2)** — the error, close to verbatim. This is what a
  reader scans for and what search matches, so use the real error text, not a
  paraphrase. Example: `Reflex build fails with "persisted lockfile is out of sync"`.
- **Symptom (`paragraph`, optionally a `code` block)** — the error as it actually
  appears in the console, verbatim. Quote the distinctive line, the one a reader
  would paste into a search box. This is the single most useful part of the
  entry; do not summarise it away.
- **Cause (`paragraph`)** — the mechanism, briefly. Why the error happens, not
  just what triggers it. Name the file and line when you traced it to one.
- **Fix (`list`, ordered)** — the steps that resolved it, in order, with the real
  commands.
- **Prevention (`paragraph`)** — how to avoid it recurring. If nothing prevents
  it, say so plainly rather than padding this section with advice you invented.

Show the user the draft, the target page, and whether that page will be created
or appended to. **Wait for confirmation.** Routing is a judgment call and
publishing changes shared team documentation — do not skip this.

### Step 2 — Read the folder tree and route

Read the live tree (see `update-doc-json` for the command and for where the
brick ID comes from — do not hardcode it).

Find the `Developer guide` folder and list its **direct subfolders**. Then route:

- If the error clearly belongs to one subfolder's domain, that is the target
  folder.
- If it is general, spans several domains, or you are unsure, the target is
  `Developer guide` itself (the fallback FAQ).

Route on the **domain the error belongs to**, not on the command that happened to
surface it. An error raised while running a CLI command, but caused by an
application's build, belongs to the application domain. Ask yourself what a
developer would call the error, not what they typed.

When two subfolders both fit, ask the user rather than picking. When none fits,
use the fallback — do **not** invent a new subfolder. Creating an FAQ page is
routine; creating a folder in the documentation tree is a structural change to
shared docs, so ask first.

### Step 3 — Find or create the FAQ page

Look inside the target folder for a page titled `FAQ`.

**If it exists:** fetch it, read it, and append your entry (Step 4).

**If it does not exist:** create it in that folder, titled `FAQ`. Capture the new
page's ID. Then give it an intro `paragraph` stating what it covers, in the same
spirit as the existing FAQ pages — one line naming the domain, so a reader
landing on it knows the scope — followed by your entry.

### Step 4 — Append the entry

Fetch the current page content and match what is already there. Existing FAQ
pages establish the house style; read one before writing so your entry does not
look like a foreign object:

- `##` for each error, `###` for sub-cases (distinct variants of the error, or
  alternative fix scenarios),
- prose that explains the cause rather than only listing steps,
- ordered `list` blocks for steps to follow.

Append the new section **at the end** of the page. Do not reorder or rewrite
existing entries.

**If the error is already documented**, do not add a second entry for it. Update
the existing section instead — the reader benefits more from one correct entry
than two competing ones. Preserve its block IDs, and tell the user you updated
rather than added.

### Step 5 — Upload and report

Upload the page (see `update-doc-json`). If the upload fails, read the error — it
validates every block, so a rejected block means the block is malformed; fix it
and retry. If it fails for another reason, surface it and **stop**. Never claim
the entry was saved when it was not.

Then tell the user:

- the page the entry landed on and its folder,
- whether the page was created or appended to,
- the heading of the entry.

## Rules

- Never save an unverified fix. An entry that does not work costs more than no
  entry at all.
- Never hardcode folder names or IDs — read the tree every time.
- Never paraphrase the error message in the symptom. Verbatim text is what makes
  the entry findable.
- Never add FAQ pages to `doc_manifest.json`.
- Never invent a fix, a cause, or a prevention step to fill a section. If you do
  not know, say you do not know.
- Always confirm the routing and the draft with the user before uploading.
- When unsure about the domain, the wording, or whether an error deserves an
  entry at all, ask the user rather than guessing.

## Task

$ARGUMENTS

# Code Review (`ruff` + `pyright` + two-axis review)

Reviews the Python changed in a brick, then gates the result on a lint and type
check that is **green** on every line the change touched. Use it before opening a
PR, or whenever the user asks to review a branch or their working tree.

Two things happen, in this order: a semantic review that reads the change, then a
mechanical gate that verifies it. The gate runs **last** because the review
produces edits, and those edits need checking too.

## Environment facts

These are not discoverable from any single file — read them before running anything.

- **Both tools are configured at the workspace root**, not per brick:
  `/lab/user/ruff.toml` and `/lab/user/pyrightconfig.json`. Always run `ruff` and
  `pyright` with `/lab/user` as the working directory, so both pick up their config
  and pyright resolves the `extraPaths` for the gws_core src roots.
- **`pyright` from the CLI reproduces Pylance in the editor.** Both run
  `typeCheckingMode: "basic"`. The editor sets `diagnosticMode: "openFilesOnly"`,
  so it only reports on open files — passing an explicit file list to the CLI is
  what makes the two agree.
- **Only `gws_core` is a git repository.** `/lab/user` is not. Resolve the brick
  first; its directory is the git root for every `git` command below.
- **The codebase is not clean.** Whole-file runs report dozens of pre-existing
  errors. Gate on lines the change touched, using the filter below — never on a
  whole-file exit code.

## Step 1 — Scope the change

Pin a **fixed point**: the commit, branch, tag, or merge-base the change is measured
against. `HEAD` reviews the uncommitted working tree. If the user did not name one,
ask.

```bash
cd /lab/user/bricks/gws_core
git rev-parse <point>          # confirm it resolves
git diff --stat <point>        # confirm the diff is non-empty
```

Stop here if the ref is bad or the diff is empty.

## Step 2 — Two-axis review

Invoke the `mattpocock-skills:code-review` skill. Supply it:

- the fixed point from step 1,
- **standards sources**: `/lab/user/CLAUDE.md` (its Best Practices section) and the
  brick's own `CLAUDE.md`. Naming these matters — the skill otherwise guesses at
  which repo files document your conventions.
- the spec or issue path, or "no spec" so it skips that axis cleanly.

It reports two axes side by side: Standards (does the code follow the documented
conventions, plus its own code-smell baseline) and Spec (does the code do what was
asked). Do not restate its rules here; it carries them.

Apply the findings you agree with. Say which you skipped and why.

If that plugin is not installed, review the two axes directly against the two
`CLAUDE.md` files instead, and say that you did.

## Step 3 — Gate to green

Re-derive the file list now, so it includes everything step 2 edited.

Write the filter below to a temp file and run it. It collects the lines the diff
touched, runs both tools, and keeps only the diagnostics that land on those lines.

```bash
cd /lab/user
python <filter>.py <point> /lab/user/bricks/gws_core
```

Fix what it reports, then run it again. **Done when it prints `CLEAN`.**

`ruff check --fix <files>` from `/lab/user` clears the mechanical ones first and
saves a pass. Type errors are fixed by hand.

If a diagnostic survives three passes, stop and report it with what you tried.
Leave it in place rather than silencing it with a `# type: ignore` or a `noqa`.

### The filter

```python
"""Filter ruff+pyright diagnostics down to lines the change actually touched."""
import json
import re
import subprocess
import sys

point = sys.argv[1]
root = "/lab/user"
brick = sys.argv[2]

diff = subprocess.run(["git", "-C", brick, "diff", "--unified=0", point],
                      capture_output=True, text=True).stdout
touched: dict[str, set[int]] = {}
cur = None
for line in diff.splitlines():
    if line.startswith("+++ b/"):
        cur = f"{brick}/{line[6:]}"
        touched.setdefault(cur, set())
    elif line.startswith("@@") and cur:
        m = re.search(r"\+(\d+)(?:,(\d+))?", line)
        if m:
            start, count = int(m.group(1)), int(m.group(2) or 1)
            touched[cur].update(range(start, start + count))

files = [f for f in touched if f.endswith(".py") and touched[f]]
if not files:
    print("no changed python lines")
    sys.exit(0)

hits = []
ruff = subprocess.run(["ruff", "check", "--output-format=concise", *files],
                      capture_output=True, text=True, cwd=root).stdout
for line in ruff.splitlines():
    m = re.match(r"(.+?):(\d+):\d+: (.+)", line)
    if m and int(m.group(2)) in touched.get(m.group(1), set()):
        hits.append(f"ruff  {m.group(1)}:{m.group(2)} {m.group(3)}")

pyr = subprocess.run(["pyright", "--outputjson", *files],
                     capture_output=True, text=True, cwd=root).stdout
for d in json.loads(pyr).get("generalDiagnostics", []):
    if d.get("severity") != "error":
        continue
    f, ln = d["file"], d["range"]["start"]["line"] + 1
    if ln in touched.get(f, set()):
        hits.append(f"pyright {f}:{ln} {d['message'].splitlines()[0]}")

print("\n".join(hits) if hits else "CLEAN")
print(f"\n{len(hits)} diagnostic(s) on changed lines")
```

## Step 4 — Report

Give the user, in one message:

- the fixed point and the number of Python files reviewed,
- the two axes from step 2, unmerged,
- the gate result: `CLEAN`, or the diagnostics that survived and what you tried.

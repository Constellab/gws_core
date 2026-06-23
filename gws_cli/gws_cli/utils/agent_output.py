"""Output helpers shared by the read-only, agent-facing CLI groups (db, resource).

These commands are designed for AI agents (e.g. Claude Code) inspecting the lab.
The conventions encoded here follow from that:

- Errors are printed to stdout (not stderr) with a concrete next action, so an
  agent reading the combined output can self-correct. ``fail`` also exits
  non-zero so scripts still see the failure.
- Output is capped (a row/char ``limit``) to avoid flooding an agent's context
  window, and JSON output is available for reliable parsing.
"""

import json
from typing import Any, NoReturn

import typer


def fail(message: str) -> NoReturn:
    """Print an agent-readable error to stdout and exit non-zero.

    Errors go to stdout (not stderr) so an agent reading combined output sees
    the message; the non-zero exit still signals failure to scripts.
    """
    typer.echo(f"ERROR: {message}")
    raise typer.Exit(code=1)


def render_value(value: Any, limit: int) -> str:
    """Render an arbitrary value for an agent, capping size for the context window.

    Complex values (notably pandas DataFrames/Series) are summarized with their
    shape plus a row-limited preview; everything else falls back to a truncated
    repr. ``limit`` is the max number of rows (for tabular values) or, very
    roughly, characters (for scalar reprs); 0 means no cap.
    """
    # Detect pandas without importing it here (keeps the CLI light and avoids a
    # hard dependency in environments where pandas is absent).
    type_path = f"{type(value).__module__}.{type(value).__qualname__}"

    if type_path == "pandas.core.frame.DataFrame":
        n_rows, n_cols = value.shape
        head = value if limit == 0 else value.head(limit)
        body = head.to_string()
        suffix = (
            f"\n... ({n_rows} rows total; showing {min(limit, n_rows)}, raise --limit for more)"
            if limit and n_rows > limit
            else f"\n({n_rows} rows)"
        )
        return f"DataFrame shape={n_rows}x{n_cols}\n{body}{suffix}"

    if type_path == "pandas.core.series.Series":
        length = len(value)
        head = value if limit == 0 else value.head(limit)
        body = head.to_string()
        suffix = (
            f"\n... ({length} values total; showing {min(limit, length)}, raise --limit for more)"
            if limit and length > limit
            else f"\n({length} values)"
        )
        return f"Series len={length}\n{body}{suffix}"

    text = repr(value)
    if limit and len(text) > limit * 80:
        cap = limit * 80
        return f"{text[:cap]}\n... (repr truncated; raise --limit for more)"
    return text


def echo_json(payload: Any) -> None:
    """Print a payload as indented JSON (str-coercing anything non-serializable)."""
    typer.echo(json.dumps(payload, indent=2, default=str, ensure_ascii=False))

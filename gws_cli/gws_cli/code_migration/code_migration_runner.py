"""Runs :class:`~gws_cli.code_migration.code_migration.CodeMigration` codemods
over a brick's source tree.

The flow is deliberately simple: describe what the migration does, list the files
it would change, and ask a single confirmation before applying to all of them.
Use ``--dry-run`` to see the full diffs, ``--yes`` to skip the confirmation.
"""

from __future__ import annotations

import difflib
import os
import traceback

import typer
from gws_core.brick.brick_settings import BrickSettings
from gws_core.core.db.version import Version

from gws_cli.code_migration.code_migration import CodeMigration, Codemod

# directories that should never be rewritten
_SKIP_DIR_NAMES = {"__pycache__", ".git", ".mypy_cache", ".pytest_cache", "node_modules", ".venv"}

GWS_CORE_BRICK_NAME = "gws_core"


# ---------------------------------------------------------------------------- #
# Source discovery
# ---------------------------------------------------------------------------- #


def iter_python_files(root_dir: str) -> list[str]:
    """List all ``.py`` files under ``root_dir`` (recursively), skipping caches."""
    py_files: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIR_NAMES]
        for name in filenames:
            if name.endswith(".py"):
                py_files.append(os.path.join(dirpath, name))
    return sorted(py_files)


# ---------------------------------------------------------------------------- #
# Brick / version helpers
# ---------------------------------------------------------------------------- #


def get_brick_gws_core_version(settings: BrickSettings) -> Version | None:
    """Return the gws_core version this brick currently targets.

    - if the brick *is* gws_core, that's its own ``version``;
    - otherwise the ``gws_core`` entry under ``environment.bricks``;
    - ``None`` if neither is available (e.g. a fresh brick with no deps).
    """
    if settings.name == GWS_CORE_BRICK_NAME and settings.version:
        return _safe_version(settings.version)
    if settings.environment and settings.environment.bricks:
        for dep in settings.environment.bricks:
            if dep.name == GWS_CORE_BRICK_NAME and dep.version:
                return _safe_version(dep.version)
    return None


def _safe_version(raw: str) -> Version | None:
    try:
        return Version(raw)
    except Exception:  # noqa: BLE001 - malformed version string in settings.json
        return None


# ---------------------------------------------------------------------------- #
# Codemod application
# ---------------------------------------------------------------------------- #


class FileChange:
    """A pending change for a single file produced by one or more codemods."""

    def __init__(
        self, path: str, display_path: str, original: str, updated: str, converted_count: int
    ) -> None:
        self.path = path  # absolute path, used for writing
        self.display_path = display_path  # relative path, used in messages / diffs
        self.original = original
        self.updated = updated
        self.converted_count = converted_count

    def unified_diff(self, context_lines: int = 3) -> str:
        diff = difflib.unified_diff(
            self.original.splitlines(keepends=True),
            self.updated.splitlines(keepends=True),
            fromfile=f"a/{self.display_path}",
            tofile=f"b/{self.display_path}",
            n=context_lines,
        )
        return "".join(diff)


class CodemodRunSummary:
    def __init__(self) -> None:
        self.changes: list[FileChange] = []
        self.warnings: list[tuple[str, str]] = []  # (path, warning)
        self.errors: list[tuple[str, str]] = []  # (path, traceback)

    @property
    def total_converted(self) -> int:
        return sum(c.converted_count for c in self.changes)


def compute_changes(
    root_dir: str, codemods: list[Codemod], display_base: str | None = None
) -> CodemodRunSummary:
    """Apply ``codemods`` (in order) to every python file under ``root_dir`` in memory.

    Nothing is written; the returned summary lists the pending :class:`FileChange`
    objects plus any warnings / errors. ``display_base`` (defaults to ``root_dir``)
    is used to compute the relative paths shown to the user.
    """
    base = display_base or root_dir
    summary = CodemodRunSummary()
    for path in iter_python_files(root_dir):
        rel_path = os.path.relpath(path, base)
        try:
            with open(path, encoding="utf-8") as fp:
                original = fp.read()
        except OSError as err:
            summary.errors.append((rel_path, f"could not read file: {err}"))
            continue

        current = original
        converted = 0
        had_error = False
        for codemod in codemods:
            try:
                current, result = codemod(current)
            except Exception:  # noqa: BLE001 - keep going on a single broken file
                summary.errors.append((rel_path, traceback.format_exc()))
                had_error = True
                break
            if result.changed:
                converted += result.converted_count
            for warning in result.warnings:
                summary.warnings.append((rel_path, warning))
        if had_error:
            continue

        if current != original:
            summary.changes.append(FileChange(path, rel_path, original, current, converted))
    return summary


# ---------------------------------------------------------------------------- #
# Applying changes
# ---------------------------------------------------------------------------- #


def _write_change(change: FileChange) -> None:
    with open(change.path, "w", encoding="utf-8") as fp:
        fp.write(change.updated)


def _apply_all(summary: CodemodRunSummary) -> int:
    for change in summary.changes:
        _write_change(change)
    return len(summary.changes)


# ---------------------------------------------------------------------------- #
# Top-level entry point
# ---------------------------------------------------------------------------- #


def _resolve_src_dir(brick_dir: str) -> str:
    """Return the brick's ``src`` directory, aborting when it does not exist."""
    src_dir = os.path.join(brick_dir, "src")
    if not os.path.isdir(src_dir):
        typer.echo(f"Error: no 'src' directory found in {brick_dir}", err=True)
        raise typer.Exit(1)
    return src_dir


def _report_errors_and_warnings(summary: CodemodRunSummary) -> None:
    """Print the files that could not be processed and the migrations left to do by hand."""
    if summary.errors:
        typer.echo("\nErrors (these files were left unchanged):", err=True)
        for path, tb in summary.errors:
            typer.echo(f"  - {path}:\n{tb}", err=True)

    if summary.warnings:
        typer.echo("\nManual migration required (not handled automatically):")
        for path, warning in summary.warnings:
            typer.echo(f"  - {path}: {warning}")


def _print_pending_changes(summary: CodemodRunSummary) -> None:
    """Print the list of files that would be updated, with their change count."""
    typer.echo(
        f"\n{len(summary.changes)} file(s) would be updated "
        f"({summary.total_converted} change(s) total):"
    )
    for change in summary.changes:
        typer.echo(f"  - {change.display_path} ({change.converted_count} change(s))")


def _print_dry_run_diffs(summary: CodemodRunSummary) -> None:
    """Print the full unified diff of every pending change (dry run output)."""
    for change in summary.changes:
        typer.echo("")
        typer.echo(f"--- {change.display_path} ---")
        typer.echo(change.unified_diff().rstrip("\n"))
    typer.echo(f"\n(dry run - no files written; {len(summary.changes)} file(s) would change)")


def run_code_migration(
    brick_dir: str,
    migration: type[CodeMigration],
    *,
    assume_yes: bool = False,
    dry_run: bool = False,
) -> None:
    """Run one code migration over a brick's ``src`` directory.

    Describes the migration, lists the impacted files, asks a single confirmation
    (unless ``assume_yes``), then applies to every file at once. With ``dry_run``
    it prints the full diffs and writes nothing.

    Raises ``typer.Exit(1)`` on error.
    """
    src_dir = _resolve_src_dir(brick_dir)

    typer.echo(f"\n>>> Code migration {migration.version}")
    typer.echo(f"    {migration.short_description}")
    typer.echo(f"    scanning {src_dir} ...")

    summary = compute_changes(src_dir, migration.get_codemods(), display_base=brick_dir)

    _report_errors_and_warnings(summary)

    if not summary.changes:
        typer.echo("\nNothing to change.")
        if summary.errors:
            raise typer.Exit(1)
        return

    _print_pending_changes(summary)

    if dry_run:
        _print_dry_run_diffs(summary)
        if summary.errors:
            raise typer.Exit(1)
        return

    if not assume_yes:
        typer.confirm(f"\nApply these changes to {len(summary.changes)} file(s)?", abort=True)

    written = _apply_all(summary)
    typer.echo(f"\nDone. {written} file(s) updated.")

    if summary.errors:
        raise typer.Exit(1)

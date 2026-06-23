"""Read-only SQL access to brick databases.

This command is intended primarily for AI agents (e.g. Claude Code) inspecting
the lab databases. Design choices that follow from that:

- Only read-only statements run (SELECT/SHOW/EXPLAIN/DESCRIBE/WITH). Every query
  also runs inside a transaction that is always rolled back, so nothing is ever
  persisted even if the guard is bypassed.
- Errors are printed to stdout (not stderr) with a concrete next action, so an
  agent reading the combined output can self-correct.
- Results are capped (``--limit``) to avoid flooding an agent's context window,
  and JSON output is available for reliable parsing.

The query/validation logic lives in :class:`DbQueryService`; this module is the
thin CLI layer (argument parsing, environment init, output formatting).
"""

from typing import Annotated

import typer
from gws_core.core.db.db_query_service import (
    DbQueryError,
    DbQueryResult,
    DbQueryService,
)
from gws_core.manage import AppManager

from gws_cli.utils.agent_output import echo_json, fail
from gws_cli.utils.cli_utils import CLIUtils

SettingsPathOption = Annotated[
    str,
    typer.Option("--settings-path", help="Path to the main settings file (advanced)."),
]

app = typer.Typer(
    help=(
        "Run read-only SQL queries against a brick database (gws_core by default).\n\n"
        "For AI agents: writes are blocked; use this to inspect schema and data.\n"
        "Start with 'gws db list' to see databases, then\n"
        '  gws db query "SHOW TABLES" --db gws_invest\n'
        '  gws db query "DESCRIBE invest_investor" --db gws_invest\n'
        '  gws db query "SELECT * FROM invest_investor" --db gws_invest --format json\n\n'
        "To inspect resources (search, RFields, views), use the 'gws resource' group."
    )
)


DEFAULT_DB = "gws_core"
DEFAULT_LIMIT = 20


def _print_table(result: DbQueryResult, rows: list[tuple], truncated: bool) -> None:
    columns = result.columns
    if not columns:
        typer.echo("(query returned no columns)")
        return

    str_rows = [[("NULL" if v is None else str(v)) for v in row] for row in rows]
    widths = [len(c) for c in columns]
    for row in str_rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def fmt_row(cells: list[str]) -> str:
        return " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(cells))

    typer.echo(fmt_row(list(columns)))
    typer.echo("-+-".join("-" * w for w in widths))
    for row in str_rows:
        typer.echo(fmt_row(row))

    suffix = " (truncated by --limit; raise --limit for more)" if truncated else ""
    typer.echo(f"\n({len(rows)} row{'s' if len(rows) != 1 else ''}){suffix}")


def _print_json(result: DbQueryResult, rows: list[tuple], truncated: bool) -> None:
    echo_json(
        {
            "columns": result.columns,
            "row_count": len(rows),
            "truncated": truncated,
            "rows": [dict(zip(result.columns, row, strict=False)) for row in rows],
        }
    )


@app.command("query", help="Execute a read-only SQL query against a brick database.")
def query(
    ctx: typer.Context,
    sql: Annotated[
        str,
        typer.Argument(help='The read-only SQL to run, e.g. "SELECT * FROM invest_investor".'),
    ],
    db_name: Annotated[
        str,
        typer.Option(
            "--db",
            help=f"Target database (brick name). Default: {DEFAULT_DB}. "
            "Run 'gws db list' for options.",
        ),
    ] = DEFAULT_DB,
    output_format: Annotated[
        str,
        typer.Option(
            "--format",
            help="Output format: 'table' (default) or 'json' (best for parsing).",
        ),
    ] = "table",
    limit: Annotated[
        int,
        typer.Option(
            "--limit",
            help=f"Max rows to print (protects the agent context window). "
            f"Default: {DEFAULT_LIMIT}. Use 0 for no limit.",
        ),
    ] = DEFAULT_LIMIT,
    settings_path: SettingsPathOption = CLIUtils.MAIN_SETTINGS_FILE_DEFAULT_PATH,
):
    if output_format not in ("table", "json"):
        fail("--format must be 'table' or 'json'.")

    # Validate before touching the (slow) env init so obvious misuse fails fast.
    try:
        DbQueryService.assert_read_only(sql)
    except DbQueryError as err:
        fail(str(err))

    # Reuse the server's init path: loads all bricks (registering their
    # DbManagers, so --db can resolve) and connects every db in dependency
    # order, so a lazy brick db is reachable by the time we query it.
    try:
        AppManager.init_gws_env_and_db(
            settings_path, log_level=CLIUtils.get_global_option_log_level(ctx)
        )
    except Exception as err:
        fail(
            f"could not initialize the lab environment: {err}. "
            "Is the lab db reachable? Try 'gws server run' first."
        )

    try:
        result = DbQueryService.execute_read_only_query(db_name, sql)
    except DbQueryError as err:
        fail(str(err))

    rows, truncated = result.limited_rows(limit)

    if output_format == "json":
        _print_json(result, rows, truncated)
    else:
        _print_table(result, rows, truncated)


@app.command("list", help="List the available brick databases (use a name with --db).")
def list_dbs(
    ctx: typer.Context,
    settings_path: SettingsPathOption = CLIUtils.MAIN_SETTINGS_FILE_DEFAULT_PATH,
):
    # Only the env/bricks are needed to enumerate managers, not db connections.
    AppManager.init_gws_env(settings_path, log_level=CLIUtils.get_global_option_log_level(ctx))
    names = DbQueryService.list_db_names()

    if not names:
        typer.echo("No databases found. The lab may not be initialized; try 'gws server run'.")
        return

    typer.echo("Available databases (pass to 'gws db query --db <name>'):\n")
    for name in names:
        typer.echo(f"  {name}")
    typer.echo(f"\nDefault when --db is omitted: {DEFAULT_DB}")

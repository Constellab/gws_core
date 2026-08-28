"""MCP tools exposing read-only SQL access to the lab's brick databases.

This is the MCP counterpart of the ``gws db`` CLI group (``gws_cli/db_cli.py``):
both are thin layers over :class:`DbQueryService`, which owns the query logic
and the read-only guard. The difference is the audience and the transport --
the CLI serves a local shell, this serves a remote MCP client (e.g. Claude Code
on a developer machine) over authenticated HTTP.

``gws_core`` reaches the lab's MCP server the same way every other brick does, through
:class:`~gws_core.mcp.mcp_registry.McpRegistry`, and gets the same treatment: its tools
are prefixed with ``gws_core_`` and carry their own ``readOnlyHint``. Nothing here is a
special case for being the brick that happens to host the server.

Design notes carried over from the CLI, which exists for the same reason (an AI
agent inspecting the lab):

- Only read-only statements run; every query is additionally wrapped in a
  transaction that is always rolled back (enforced in ``DbQueryService``).
- Errors are returned as readable text with a concrete next action, so the
  calling agent can self-correct instead of failing opaquely.
- Results are capped (``limit``) to protect the agent's context window.

Authentication is handled entirely by the transport layer (see
``mcp_token_verifier``): by the time a tool below runs, the caller is already
authenticated as a lab user. These two tools need nothing beyond that, because
read-only SQL over the lab's own databases is what every lab user may already do
through the CLI -- a tool exposing more than its caller may see would have to check
that itself.
"""

from typing import Any

from mcp.types import ToolAnnotations

from gws_core.brick.brick_helper import BrickHelper
from gws_core.core.db.db_query_service import DbQueryError, DbQueryService
from gws_core.mcp.mcp_registry import McpRegistry

DEFAULT_DB = "gws_core"
DEFAULT_LIMIT = 20

# Each tool's description points at the other, and must name it as the client sees it --
# 'db_list' alone names a tool that does not exist. Asked of the registry rather than
# written out, so the prefixing rule stays in one place.
DB_LIST_TOOL_NAME = McpRegistry.build_tool_name(BrickHelper.GWS_CORE, "db_list")
DB_QUERY_TOOL_NAME = McpRegistry.build_tool_name(BrickHelper.GWS_CORE, "db_query")

# Both tools only read. Declared here rather than promised by the server: the server
# serves whatever the installed bricks declare, so it cannot speak for them.
READ_ONLY = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    # The lab's own databases: a closed, known set, not an open-ended remote.
    openWorldHint=False,
)


@McpRegistry.register_tool(
    "db_list",
    title="List lab databases",
    description=(
        "List the available brick databases.\n\n"
        "Returns the database names that can be passed as the 'db' argument of "
        f"{DB_QUERY_TOOL_NAME}. "
        "The default database when 'db' is omitted is 'gws_core'."
    ),
    annotations=READ_ONLY,
)
def db_list() -> list[str]:
    """Return the names of all registered brick databases."""
    return DbQueryService.list_db_names()


@McpRegistry.register_tool(
    "db_query",
    title="Run a read-only SQL query",
    description=(
        "Execute a read-only SQL query against a brick database.\n\n"
        "Only SELECT/SHOW/EXPLAIN/DESCRIBE/WITH statements are allowed; any attempt to "
        "modify data is rejected. A single statement per call (no ';' separators).\n\n"
        "Args:\n"
        "  sql: The read-only SQL to run, e.g. 'SELECT * FROM invest_investor'.\n"
        "  db: Target database (brick name). Defaults to 'gws_core'. "
        f"Use {DB_LIST_TOOL_NAME} to see options.\n"
        "  limit: Max rows returned (protects your context window). "
        "Default 20, 0 for no limit.\n\n"
        "Returns a dict with 'columns', 'row_count', 'truncated' and 'rows' "
        "(a list of column->value objects).\n\n"
        "Typical sequence:\n"
        f'  {DB_QUERY_TOOL_NAME}(sql="SHOW TABLES", db="gws_invest")\n'
        f'  {DB_QUERY_TOOL_NAME}(sql="DESCRIBE invest_investor", db="gws_invest")\n'
        f'  {DB_QUERY_TOOL_NAME}(sql="SELECT * FROM invest_investor", db="gws_invest")'
    ),
    annotations=READ_ONLY,
)
def db_query(
    sql: str,
    db: str = DEFAULT_DB,
    limit: int = DEFAULT_LIMIT,
) -> dict[str, Any]:
    """Run a read-only query and return the rows as JSON-friendly dicts.

    :param sql: The read-only SQL to run.
    :param db: Brick name of the target database.
    :param limit: Max rows to return, ``0`` for no limit.
    :raises ValueError: If the SQL is rejected or the query fails. The message is
        agent-readable and states the next action.
    """
    try:
        result = DbQueryService.execute_read_only_query(db, sql)
    except DbQueryError as err:
        # Surface the service's actionable message to the agent rather than a stack trace.
        raise ValueError(str(err)) from err

    rows, truncated = result.limited_rows(limit)

    return {
        "columns": result.columns,
        "row_count": len(rows),
        "truncated": truncated,
        "rows": [dict(zip(result.columns, row, strict=False)) for row in rows],
    }

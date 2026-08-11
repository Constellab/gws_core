"""MCP tools exposing read-only SQL access to the lab's brick databases.

This is the MCP counterpart of the ``gws db`` CLI group (``gws_cli/db_cli.py``):
both are thin layers over :class:`DbQueryService`, which owns the query logic
and the read-only guard. The difference is the audience and the transport --
the CLI serves a local shell, this serves a remote MCP client (e.g. Claude Code
on a developer machine) over authenticated HTTP.

Design notes carried over from the CLI, which exists for the same reason (an AI
agent inspecting the lab):

- Only read-only statements run; every query is additionally wrapped in a
  transaction that is always rolled back (enforced in ``DbQueryService``).
- Errors are returned as readable text with a concrete next action, so the
  calling agent can self-correct instead of failing opaquely.
- Results are capped (``limit``) to protect the agent's context window.

Authentication is handled entirely by the transport layer (see
``mcp_token_verifier``): by the time a tool below runs, the caller is already
authenticated as a lab user.
"""

from typing import Any

from mcp.server.auth.provider import OAuthAuthorizationServerProvider
from mcp.server.auth.settings import AuthSettings
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from gws_core.core.db.db_query_service import DbQueryError, DbQueryService

DEFAULT_DB = "gws_core"
DEFAULT_LIMIT = 20

INSTRUCTIONS = (
    "This server gives read-only SQL access to the Constellab lab's brick databases.\n\n"
    "Writes are blocked: use it to inspect schema and data.\n"
    "Start with db_list to see the available databases, then use db_query, e.g.\n"
    '  db_query(sql="SHOW TABLES", db="gws_invest")\n'
    '  db_query(sql="DESCRIBE invest_investor", db="gws_invest")\n'
    '  db_query(sql="SELECT * FROM invest_investor", db="gws_invest")'
)


def _build_transport_security(allowed_hosts: list[str] | None) -> TransportSecuritySettings:
    """Configure the SDK's DNS-rebinding protection for the lab's own host.

    The SDK defaults to ``enable_dns_rebinding_protection=True`` with an **empty**
    ``allowed_hosts``, which rejects every request that is not to localhost with
    ``421 Invalid Host header``. That default suits a server bound to a loopback
    port; the lab is served on its own domain, so the domain must be declared or
    no client can ever connect.

    The protection is kept on (it stops a malicious page from pointing a rebound
    DNS name at the lab) and simply told the truth about where the lab lives.

    :param allowed_hosts: Host headers to accept, without scheme. ``None`` or empty
        turns the protection off, for deployments where the host is not knowable.
    """
    if not allowed_hosts:
        return TransportSecuritySettings(enable_dns_rebinding_protection=False)

    # Accept the host with or without an explicit port.
    hosts = [host for entry in allowed_hosts for host in (entry, f"{entry}:*")]

    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=hosts,
        # Browsers never call this API directly (an MCP client is not a page), so
        # requests legitimately carry no Origin. Listing the same hosts keeps a
        # browser-based client working without widening what is accepted.
        allowed_origins=[f"https://{entry}" for entry in allowed_hosts]
        + [f"http://{entry}" for entry in allowed_hosts],
    )


def db_list() -> list[str]:
    """Return the names of all registered brick databases."""
    return DbQueryService.list_db_names()


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


def build_mcp_server(
    auth_provider: OAuthAuthorizationServerProvider,
    auth_settings: AuthSettings,
    allowed_hosts: list[str] | None = None,
) -> FastMCP:
    """Build the MCP server with its tools and authentication wired in.

    Built by a function rather than at import time because the auth configuration
    depends on ``Settings`` (the lab's URL), which is not loaded when this module
    is imported.

    Passing only ``auth_server_provider`` (never ``token_verifier`` as well -- the
    SDK rejects both) makes the SDK derive its verifier from the provider's
    ``load_access_token``, which is where the lab JWT is validated.

    :param auth_provider: The OAuth provider issuing and verifying tokens.
    :param auth_settings: The OAuth settings (issuer / resource URLs, DCR).
    :param allowed_hosts: Host headers this server answers to (see
        :func:`_build_transport_security`). Defaults to no host restriction.
    :return: The configured MCP server.
    """
    mcp = FastMCP(
        "gws-lab",
        instructions=INSTRUCTIONS,
        auth_server_provider=auth_provider,
        auth=auth_settings,
        transport_security=_build_transport_security(allowed_hosts),
    )

    mcp.add_tool(
        db_list,
        name="db_list",
        title="List lab databases",
        description=(
            "List the available brick databases.\n\n"
            "Returns the database names that can be passed as the 'db' argument of db_query. "
            "The default database when 'db' is omitted is 'gws_core'."
        ),
    )

    mcp.add_tool(
        db_query,
        name="db_query",
        title="Run a read-only SQL query",
        description=(
            "Execute a read-only SQL query against a brick database.\n\n"
            "Only SELECT/SHOW/EXPLAIN/DESCRIBE/WITH statements are allowed; any attempt to "
            "modify data is rejected. A single statement per call (no ';' separators).\n\n"
            "Args:\n"
            "  sql: The read-only SQL to run, e.g. 'SELECT * FROM invest_investor'.\n"
            "  db: Target database (brick name). Defaults to 'gws_core'. "
            "Use db_list to see options.\n"
            "  limit: Max rows returned (protects your context window). "
            "Default 20, 0 for no limit.\n\n"
            "Returns a dict with 'columns', 'row_count', 'truncated' and 'rows' "
            "(a list of column->value objects)."
        ),
    )

    return mcp

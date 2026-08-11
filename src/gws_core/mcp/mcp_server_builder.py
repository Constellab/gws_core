"""Builds the lab's single MCP server from the tools its bricks declared.

The tools themselves live in the bricks (``gws_core``'s own are in
:mod:`gws_core.mcp.db_mcp`); this module only assembles what
:class:`~gws_core.mcp.mcp_registry.McpRegistry` collected at brick import, and wires
in the transport security and the authentication the mount needs.

The server describes itself from that registry rather than from a fixed text: the tool
set is a function of which bricks are installed, so no statement about the tools as a
whole can be written ahead of time.
"""

from mcp.server.auth.provider import OAuthAuthorizationServerProvider
from mcp.server.auth.settings import AuthSettings
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from gws_core.core.utils.logger import Logger
from gws_core.mcp.mcp_registry import McpBrickContribution, McpRegistry

SERVER_NAME = "gws-lab"


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


def build_instructions(contributions: list[McpBrickContribution]) -> str:
    """Describe the server from the bricks contributing to it.

    Says what the client cannot work out on its own -- that a name's first segment is
    the brick that declared it, and which bricks are present -- and nothing more.

    Deliberately absent: any claim about what the tools do or do not do. The lab used
    to promise the whole server was read-only, which stopped being true the moment a
    brick declared a mutating tool. Those properties are the tools' to state, through
    their ``readOnlyHint`` annotation and their descriptions, and are not restated here:
    the client already reads them, and two sources of truth diverge the day a brick
    changes an annotation without touching this text.

    :param contributions: The declared tools, grouped by brick.
    """
    if not contributions:
        return (
            "This Constellab lab serves no MCP tool: none of its installed bricks declares one."
        )

    lines = [
        "This server exposes the MCP tools declared by the bricks installed in this "
        "Constellab lab.",
        "",
        "Each tool name is prefixed with the name of the brick that declared it. What a tool "
        "does, and whether it changes anything, is stated by the tool itself: read its "
        "description and its annotations.",
        "",
        "Bricks contributing tools:",
    ]

    for contribution in contributions:
        version = f" {contribution.brick_version}" if contribution.brick_version else ""
        tool_names = ", ".join(tool.name for tool in contribution.tools)
        lines.append(f"  - {contribution.brick_name}{version}: {tool_names}")

    return "\n".join(lines)


def build_mcp_server(
    auth_provider: OAuthAuthorizationServerProvider,
    auth_settings: AuthSettings,
    allowed_hosts: list[str] | None = None,
) -> FastMCP:
    """Build the MCP server with the registered tools and authentication wired in.

    Built by a function rather than at import time for two reasons: the auth
    configuration depends on ``Settings`` (the lab's URL), which is not loaded when this
    module is imported, and the registry is only complete once every brick has been
    imported.

    Passing only ``auth_server_provider`` (never ``token_verifier`` as well -- the
    SDK rejects both) makes the SDK derive its verifier from the provider's
    ``load_access_token``, which is where the lab JWT is validated.

    :param auth_provider: The OAuth provider issuing and verifying tokens.
    :param auth_settings: The OAuth settings (issuer / resource URLs, DCR).
    :param allowed_hosts: Host headers this server answers to (see
        :func:`_build_transport_security`). Defaults to no host restriction.
    :return: The configured MCP server.
    """
    contributions = McpRegistry.get_contributions()

    mcp = FastMCP(
        SERVER_NAME,
        instructions=build_instructions(contributions),
        auth_server_provider=auth_provider,
        auth=auth_settings,
        transport_security=_build_transport_security(allowed_hosts),
    )

    for contribution in contributions:
        for tool in contribution.tools:
            tool.add_to_server(mcp)

    tool_count = sum(len(contribution.tools) for contribution in contributions)
    Logger.info(
        f"MCP server serving {tool_count} tool(s) from {len(contributions)} brick(s): "
        f"{', '.join(contribution.brick_name for contribution in contributions)}"
    )

    return mcp

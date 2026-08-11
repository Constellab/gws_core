"""What the lab tells its own front-end about the Claude Code plugin it serves.

The lab's screen and the served manifest describe **one** generation: the names, the
version and the commands below are read from the plugin the lab is handing out at that
moment, never rebuilt from the naming rules a second time. A screen telling a user to
install ``mon-lab`` while the marketplace declares something else would be worse than no
screen at all.
"""

from enum import Enum

from gws_core.core.model.model_dto import BaseModelDTO


class ClaudePluginStatus(Enum):
    """Whether this lab can hand out a Claude Code plugin, and why not when it cannot.

    The front-end shows the commands for ``AVAILABLE`` and an explanation otherwise; the
    two failing cases have different audiences, so they are distinct values rather than a
    boolean plus a message.
    """

    # The plugin is served: the commands below work.
    AVAILABLE = "AVAILABLE"
    # The lab's MCP server is off, so there is nothing to connect to and no route serving
    # a manifest. An administrator decides this.
    MCP_DISABLED = "MCP_DISABLED"
    # The lab is reachable only over http, or on a loopback host. Claude Code refuses such
    # an archive URL outright. This is the normal state of a local development lab.
    URL_NOT_SUPPORTED = "URL_NOT_SUPPORTED"


class ClaudePluginCommandsDTO(BaseModelDTO):
    """The commands a user types in Claude Code, ready to be copied.

    Built by the lab rather than assembled by the front-end: the plugin and marketplace
    names follow rules (slug, id suffix, rename history) that only the lab applies, and a
    second implementation of them would drift.
    """

    add_marketplace: str
    install: str
    update_marketplace: str
    update_plugin: str


class ClaudePluginInfoDTO(BaseModelDTO):
    """Everything the lab's "connect Claude Code" screen needs.

    Every field but the first three is ``None`` unless the status is ``AVAILABLE``: a lab
    that serves no plugin has no name, no version and no URL to show.
    """

    status: ClaudePluginStatus
    lab_name: str
    # Below this version, Claude Code cannot install a plugin distributed this way.
    minimum_claude_code_version: str

    marketplace_name: str | None = None
    marketplace_url: str | None = None
    plugin_name: str | None = None
    version: str | None = None
    mcp_url: str | None = None
    commands: ClaudePluginCommandsDTO | None = None

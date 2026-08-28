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
    # an archive URL outright. This is the normal state of a local development lab, and the
    # one status that carries ``dev_install`` instead of ``commands``.
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


class ClaudePluginDevInstallDTO(BaseModelDTO):
    """The fallback for a lab Claude Code will not download from: install from a folder.

    Carried only by ``URL_NOT_SUPPORTED``. The user runs one shell command and restarts
    Claude Code: the script downloads the archive, writes a local marketplace, and registers
    both through the ``claude`` CLI. ``install`` and ``update_marketplace`` are the manual
    fallback for a machine where that CLI is not on the PATH -- the script prints them
    itself, numbered, when it needs them.

    Self-contained on purpose: the names in here belong to the **local** marketplace, not to
    the lab's own one, and a screen mixing the two would tell a user to install from a
    marketplace that cannot work.

    :param posix_command: The one-liner for macOS, Linux and WSL.
    :param windows_command: The one-liner for PowerShell.
    :param posix_script_url: Where the bash script is served, for a user who wants to read
        it before piping it into a shell.
    :param windows_script_url: Where the PowerShell script is served.
    :param plugin_name: The plugin's name -- the same one the lab serves.
    :param version: The version the script installs right now.
    :param marketplace_name: The name of the local marketplace the script writes.
    :param install: The Claude Code command that installs from it. Only needed when the
        script could not use the ``claude`` CLI, and only *after*
        ``/plugin marketplace add`` -- on its own it answers "Marketplace not found".
    :param update_marketplace: Makes Claude Code re-read the folder. The script runs it too;
        it is here for the same manual fallback.
    """

    posix_command: str
    windows_command: str
    posix_script_url: str
    windows_script_url: str
    plugin_name: str
    version: str
    marketplace_name: str
    install: str
    update_marketplace: str


class ClaudePluginInfoDTO(BaseModelDTO):
    """Everything the lab's "connect Claude Code" screen needs.

    Which of the two command blocks is filled follows the status, and they are never both
    set:

    - ``AVAILABLE``: every field, and ``commands``.
    - ``URL_NOT_SUPPORTED``: ``dev_install``, and nothing else. The lab's own marketplace
      name and URL stay empty -- they name a channel that cannot work here.
    - ``MCP_DISABLED``: the first three fields only. There is no plugin at all, so no name
      and no version exist to show.
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
    dev_install: ClaudePluginDevInstallDTO | None = None

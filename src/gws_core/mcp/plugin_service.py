"""Describes the lab's Claude Code plugin to the lab's own front-end.

The public routes (:mod:`gws_core.mcp.plugin_controller`) hand the plugin to Claude Code.
This describes it to a human, on the lab's screen: which commands to run, which version is
being served, and -- when nothing is being served -- why.

It reads the same generation the marketplace serves, so the screen and the manifest can
never name different things.
"""

from urllib.parse import urlparse

from gws_core.core.utils.settings import Settings
from gws_core.mcp.mcp_controller import get_lab_base_url
from gws_core.mcp.plugin_dto import (
    ClaudePluginCommandsDTO,
    ClaudePluginInfoDTO,
    ClaudePluginStatus,
)
from gws_core.mcp.plugin_generator import PluginGenerator, build_marketplace_url

# The first Claude Code version able to install a plugin from an ``archive`` source.
# Below it the install fails with an explicit message; below 2.1.120 the marketplace does
# not load at all, which the lower bound covers.
MINIMUM_CLAUDE_CODE_VERSION = "2.1.224"

# Hosts Claude Code refuses in an archive URL, whatever the scheme.
_LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}


class PluginService:
    """The lab's own view of the plugin it distributes."""

    @classmethod
    def get_plugin_info(cls) -> ClaudePluginInfoDTO:
        """Describe the plugin, or say why there is none.

        Nothing is generated when the plugin cannot be installed: a lab with its MCP
        server off must not record a plugin name it never served, and a lab on http has
        nothing a client could accept anyway.
        """
        lab_name = Settings.get_lab_name()
        status = cls.get_status()

        if status is not ClaudePluginStatus.AVAILABLE:
            return ClaudePluginInfoDTO(
                status=status,
                lab_name=lab_name,
                minimum_claude_code_version=MINIMUM_CLAUDE_CODE_VERSION,
            )

        # The very generation the marketplace route serves, cached with its archive.
        generated = PluginGenerator.get_generated()
        marketplace_name = generated.identity.marketplace_name
        plugin_name = generated.identity.plugin_name
        marketplace_url = build_marketplace_url()

        return ClaudePluginInfoDTO(
            status=status,
            lab_name=lab_name,
            minimum_claude_code_version=MINIMUM_CLAUDE_CODE_VERSION,
            marketplace_name=marketplace_name,
            marketplace_url=marketplace_url,
            plugin_name=plugin_name,
            version=generated.version,
            mcp_url=generated.mcp_url,
            commands=ClaudePluginCommandsDTO(
                add_marketplace=f"/plugin marketplace add {marketplace_url}",
                install=f"/plugin install {plugin_name}@{marketplace_name}",
                update_marketplace=f"/plugin marketplace update {marketplace_name}",
                update_plugin=f"/plugin update {plugin_name}",
            ),
        )

    @classmethod
    def get_status(cls) -> ClaudePluginStatus:
        """Whether the plugin can be installed from this lab, and why not when it cannot."""
        if not Settings.is_mcp_server_enabled():
            return ClaudePluginStatus.MCP_DISABLED

        if not cls.url_is_supported(get_lab_base_url()):
            return ClaudePluginStatus.URL_NOT_SUPPORTED

        return ClaudePluginStatus.AVAILABLE

    @classmethod
    def url_is_supported(cls, lab_url: str) -> bool:
        """Whether Claude Code would accept an archive served from this lab's URL.

        It refuses anything that is not ``https``, and any loopback or link-local host --
        which is every local development lab. Checked here so the screen says so plainly,
        instead of the user meeting the refusal halfway through an install.
        """
        parsed = urlparse(lab_url)

        return parsed.scheme == "https" and parsed.hostname not in _LOOPBACK_HOSTS

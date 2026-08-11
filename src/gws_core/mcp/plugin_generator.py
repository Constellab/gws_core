"""Generates the Claude Code plugin this lab distributes.

A plugin published from a repository describes a fixed set of tools. The set a lab
actually serves is a function of *which bricks are installed and at which versions*, so
two labs on the same ``gws_core`` expose different surfaces. Only the lab knows its own
surface, which is why the lab generates its own plugin instead of installing one.

What is generated is two things that must always agree:

- the **marketplace manifest**, served at a URL that never changes, which names the
  plugin, its version, and where to download it;
- the **archive**, a zip holding ``.claude-plugin/plugin.json`` (which points Claude Code
  at this lab's MCP endpoint) and the skills the contributing bricks ship.

Both come out of a single generation, cached in memory: a manifest announcing a version
whose archive says something else is the one failure mode with no legible symptom.

The version is ``<gws_core version>+<fingerprint of the generated content>``. Hashing the
*brick versions* instead would churn every lab's plugin on any brick release, even one
that touched no tool -- and, decisively, would not change when the lab is renamed, leaving
clients holding a plugin whose name the manifest no longer lists. The lab's name is part
of the content, so a rename propagates through the ordinary update path.

**Everything generated here is public.** It is served unauthenticated, to anyone who
knows the lab's URL. Hence the manifest carries a fingerprint rather than the list of
installed bricks and their versions.
"""

import hashlib
import io
import json
import zipfile
from dataclasses import dataclass
from threading import Lock
from typing import Any

from mcp.server.fastmcp.tools import Tool as FastMcpTool

from gws_core.brick.brick_helper import BrickHelper
from gws_core.core.utils.logger import Logger
from gws_core.mcp.mcp_controller import get_lab_base_url, get_mcp_url
from gws_core.mcp.mcp_registry import McpRegistry, McpToolDeclaration
from gws_core.mcp.plugin_identity import PluginIdentity, resolve_identity
from gws_core.mcp.plugin_skills import PluginSkill, collect_skills

# Route the archive and the manifest are served from.
PLUGINS_ROUTE_PATH = "plugins"
MARKETPLACE_FILE_NAME = "marketplace.json"

# Where Claude Code looks for a plugin's manifest inside the archive.
PLUGIN_MANIFEST_FOLDER = ".claude-plugin"
PLUGIN_MANIFEST_FILE_NAME = "plugin.json"

# The key the lab's MCP server takes in the plugin. It is part of the tool permission ids
# users write (``mcp__<plugin>_<server>__<tool>``), so it is a constant: the plugin name
# already carries which lab this is.
MCP_SERVER_KEY = "constellab"

MARKETPLACE_SCHEMA_URL = "https://anthropic.com/claude-code/marketplace.schema.json"

# How much of the content hash goes into the version. Collisions here would hide an
# update; 8 hex characters make that a non-event next to the number of versions a lab
# ever serves.
FINGERPRINT_LENGTH = 8

# Fixed timestamp for every archive entry. Zip stores a modification time per file, so
# without this the same content would produce different bytes on every generation.
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


@dataclass(frozen=True)
class GeneratedPlugin:
    """One generation: a manifest and the archive it points at, of the same content.

    :param identity: The names this lab serves.
    :param version: The plugin version, in both the manifest and ``plugin.json``.
    :param archive_file_name: File name of the archive, version included.
    :param marketplace_manifest: The marketplace manifest, ready to serialize.
    :param archive: The zip archive's bytes.
    """

    identity: PluginIdentity
    version: str
    archive_file_name: str
    marketplace_manifest: dict[str, Any]
    archive: bytes


class PluginGenerator:
    """Generates the lab's plugin once, and serves it from memory afterwards.

    Nothing the generation reads can change while the lab runs: the MCP registry is
    complete once the bricks are imported, and the lab's name and id come from the
    environment. The lab runs uvicorn single-process, so one cache is the whole lab's
    cache.
    """

    _generated: GeneratedPlugin | None = None
    _lock = Lock()

    @classmethod
    def get_generated(cls) -> GeneratedPlugin:
        """The generated plugin, built on the first call.

        Built under a lock so two simultaneous first requests do not each pay for an
        archive, and cannot end up reading two different generations.
        """
        if cls._generated is not None:
            return cls._generated

        with cls._lock:
            if cls._generated is None:
                cls._generated = cls.generate()
                Logger.info(
                    f"Claude Code plugin '{cls._generated.identity.plugin_name}' generated "
                    f"in version {cls._generated.version}"
                )

        return cls._generated

    @classmethod
    def clear_cache(cls) -> None:
        """Drop the generated plugin so the next call rebuilds it. Useful for tests."""
        with cls._lock:
            cls._generated = None

    @classmethod
    def generate(cls) -> GeneratedPlugin:
        """Generate the manifest and the archive, without touching the cache."""
        identity = resolve_identity()
        contributions = McpRegistry.get_contributions()
        tools = [tool for contribution in contributions for tool in contribution.tools]
        skills = collect_skills(
            [contribution.brick_name for contribution in contributions], identity.lab_name
        )

        mcp_url = get_mcp_url()
        version = build_version(identity, mcp_url, tools, skills)
        plugin_manifest = build_plugin_manifest(identity, version, mcp_url, skills)
        archive_file_name = build_archive_file_name(identity.plugin_name, version)

        return GeneratedPlugin(
            identity=identity,
            version=version,
            archive_file_name=archive_file_name,
            marketplace_manifest=build_marketplace_manifest(identity, version, archive_file_name),
            archive=build_archive(plugin_manifest, skills),
        )


def build_version(
    identity: PluginIdentity,
    mcp_url: str,
    tools: list[McpToolDeclaration],
    skills: list[PluginSkill],
) -> str:
    """``<gws_core version>+<fingerprint>``, stable for as long as the content is.

    The fingerprint covers what a client can see: the identity, the endpoint, every
    tool's name, title, description and schema, and every skill file.

    What it deliberately leaves out is each tool's ``meta``, which carries the declaring
    brick's version. Including it would move the fingerprint on every brick release, for
    a tool nobody touched -- the churn this scheme exists to avoid.
    """
    payload = {
        "marketplace": identity.marketplace_name,
        "plugin": identity.plugin_name,
        "lab_name": identity.lab_name,
        "renames": identity.build_renames(),
        "mcp_url": mcp_url,
        "tools": [
            {
                "name": tool.name,
                "title": tool.title,
                "description": tool.description,
                "annotations": tool.annotations.model_dump(mode="json")
                if tool.annotations
                else None,
                "schema": _build_tool_schema(tool),
            }
            for tool in tools
        ],
        "skills": [
            {
                "path": skill.archive_path,
                "files": {
                    path: hashlib.sha256(content).hexdigest()
                    for path, content in skill.files.items()
                },
            }
            for skill in skills
        ],
    }
    fingerprint = hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()

    gws_core_version = BrickHelper.get_gws_core_version() or "0.0.0"

    return f"{gws_core_version}+{fingerprint[:FINGERPRINT_LENGTH]}"


def build_archive_file_name(plugin_name: str, version: str) -> str:
    """The archive's file name. It carries the version, so its URL changes with it.

    That is what stops a proxy or a CDN from answering a new version's URL with the zip
    it cached for the previous one.
    """
    return f"{plugin_name}-{version}.zip"


def build_archive_url(archive_file_name: str) -> str:
    """The absolute URL the manifest points at, on the lab's own domain."""
    return f"{get_lab_base_url()}/{PLUGINS_ROUTE_PATH}/{archive_file_name}"


def build_marketplace_manifest(
    identity: PluginIdentity, version: str, archive_file_name: str
) -> dict[str, Any]:
    """The manifest served at the URL the user adds once.

    It declares a single plugin -- this lab -- and where to download it. There is no
    ``userConfig``: the lab knows where it is, so nobody can point the plugin at the
    wrong host.
    """
    manifest: dict[str, Any] = {
        "$schema": MARKETPLACE_SCHEMA_URL,
        "name": identity.marketplace_name,
        "owner": {"name": identity.lab_name},
        "description": f"The Claude Code plugin served by the Constellab lab '{identity.lab_name}'.",
        "plugins": [
            {
                "name": identity.plugin_name,
                "description": _build_plugin_description(identity),
                # Declared here as well as in plugin.json so Claude Code can see that an
                # update exists without downloading the archive.
                "version": version,
                "source": {
                    "source": "archive",
                    "url": build_archive_url(archive_file_name),
                },
            }
        ],
    }

    renames = identity.build_renames()
    if renames:
        manifest["renames"] = renames

    return manifest


def build_plugin_manifest(
    identity: PluginIdentity, version: str, mcp_url: str, skills: list[PluginSkill]
) -> dict[str, Any]:
    """``plugin.json``: what the plugin is, and the one MCP server it connects to."""
    manifest: dict[str, Any] = {
        "name": identity.plugin_name,
        "displayName": identity.lab_name,
        "version": version,
        "description": _build_plugin_description(identity),
        # The lab is the author: it is the machine the plugin talks to, and the only
        # party that can answer for what the plugin exposes.
        "author": {"name": identity.lab_name},
        "mcpServers": {
            MCP_SERVER_KEY: {
                "type": "http",
                "url": mcp_url,
            }
        },
    }

    # Declared explicitly because the skills sit one folder deeper than the auto-loaded
    # ``skills/`` layout: each brick gets its own sub-folder, so two bricks may ship a
    # skill under the same name.
    if skills:
        manifest["skills"] = [skill.manifest_path for skill in skills]

    return manifest


def build_archive(plugin_manifest: dict[str, Any], skills: list[PluginSkill]) -> bytes:
    """Assemble the zip: the manifest at the top, then the skills.

    Claude Code looks for ``.claude-plugin/`` at the top of the archive or inside a
    single wrapping folder, no deeper -- so the manifest goes at the root.

    Assembly is deterministic (fixed order, fixed timestamps), which is what lets the
    same content be recognised as the same version.
    """
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        _write_archive_file(
            archive,
            f"{PLUGIN_MANIFEST_FOLDER}/{PLUGIN_MANIFEST_FILE_NAME}",
            (json.dumps(plugin_manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8"),
        )

        for skill in skills:
            for relative_path, content in skill.files.items():
                _write_archive_file(archive, f"{skill.archive_path}/{relative_path}", content)

    return buffer.getvalue()


def _write_archive_file(archive: zipfile.ZipFile, path: str, content: bytes) -> None:
    """Write one file with a fixed timestamp and fixed permissions."""
    info = zipfile.ZipInfo(path, date_time=ZIP_TIMESTAMP)
    # 0o644, in the high 16 bits where zip keeps the unix mode.
    info.external_attr = 0o644 << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    archive.writestr(info, content)


def _build_plugin_description(identity: PluginIdentity) -> str:
    """What the plugin offers, without naming a single brick: the manifest is public."""
    return (
        f"The MCP tools and skills of the Constellab lab '{identity.lab_name}'. "
        "Its tool set depends on the bricks installed in that lab."
    )


def _build_tool_schema(tool: McpToolDeclaration) -> dict[str, Any]:
    """The tool's input schema, as the MCP client will receive it.

    Derived the same way the server derives it, from the function's signature, so the
    fingerprint moves when a tool's arguments change.
    """
    fast_tool = FastMcpTool.from_function(
        tool.function,
        name=tool.name,
        title=tool.title,
        description=tool.description,
        annotations=tool.annotations,
        icons=tool.icons,
        meta=tool.meta,
        structured_output=tool.structured_output,
    )
    return fast_tool.parameters


def build_marketplace_url() -> str:
    """The URL a user adds once, which never changes for the life of the lab."""
    return f"{get_lab_base_url()}/{PLUGINS_ROUTE_PATH}/{MARKETPLACE_FILE_NAME}"

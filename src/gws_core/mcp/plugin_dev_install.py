"""Generates the script that installs this lab's plugin from a local folder.

A lab on ``http://localhost`` cannot hand out its plugin through the marketplace channel:
Claude Code refuses an ``archive`` source that is not ``https`` on a non-loopback host (see
:meth:`gws_core.mcp.plugin_service.PluginService.url_is_supported`). The lab still *serves*
the archive perfectly well -- what it cannot do is have Claude Code fetch it itself.

So the download moves to the machine Claude Code runs on. That machine reaches the lab over
the published port even when the lab is in a container whose filesystem it cannot see, which
is the ordinary development setup: the script curls the archive, unpacks it under the user's
home, and writes a second marketplace beside it whose plugin source is a **local path** --
the one source type with no scheme requirement.

It then registers that marketplace and installs the plugin through the ``claude`` CLI, so
there is nothing left to paste. Leaving those two commands to the user cost exactly what
telling a user to run two ordered commands always costs: ``/plugin install`` alone answers
*Marketplace not found*, which reads as a broken plugin rather than a skipped step. When the
CLI is not on the PATH the script says what to run, numbered, and names that error.

Two scripts, because there is no shell all three platforms run: ``bash`` for macOS and
Linux, PowerShell for Windows. They do the same things in the same order, and both are
generated here so the pair cannot drift.

**The lab generates them, so nothing needs parsing client-side.** The plugin name, the
version, the archive URL and the marketplace JSON are baked in as literals. That is what
keeps the scripts free of a JSON parser -- ``jq`` is not installable-by-assumption on any of
the three platforms -- and it is the whole reason this is a route rather than a snippet in
the documentation.

The generated content is public, exactly like the archive and the manifest it names.
"""

import json
from dataclasses import dataclass
from typing import Any

from gws_core.mcp.plugin_generator import (
    MARKETPLACE_SCHEMA_URL,
    GeneratedPlugin,
    PluginGenerator,
    build_plugins_url,
)

# Served from the plugins route, beside the manifest and the archive.
POSIX_SCRIPT_FILE_NAME = "install-dev.sh"
WINDOWS_SCRIPT_FILE_NAME = "install-dev.ps1"

# Appended to the lab's real marketplace name. A local install never updates itself, so it
# must not answer to the name the lab's own marketplace uses: a developer who later adds
# the real one would otherwise have two marketplaces claiming one name.
DEV_MARKETPLACE_SUFFIX = "-dev"

# Where the scripts install, under the user's home. One folder per lab marketplace, so two
# labs can be installed side by side.
INSTALL_FOLDER = ".constellab/claude-plugins"

# The bash heredoc terminator for the embedded manifest. PowerShell's here-string
# terminator is fixed by the language (``'@``) and cannot be chosen.
#
# Neither can be closed early by the manifest, whatever the lab is called: json.dumps
# escapes newlines inside values, so every line of the JSON is a key or a bracket and none
# can be a terminator standing alone.
JSON_TERMINATOR = "CONSTELLAB_MARKETPLACE_JSON"


def quote_for_bash(value: str) -> str:
    """Wrap a value in single quotes bash reads literally.

    The values baked into the scripts come from the environment (``LAB_NAME``, the lab's
    API URL), so a lone apostrophe in one of them would otherwise end the quoting and turn
    the rest of the line into code.
    """
    return "'" + value.replace("'", "'\\''") + "'"


def quote_for_powershell(value: str) -> str:
    """Wrap a value in single quotes PowerShell reads literally, doubling any apostrophe."""
    return "'" + value.replace("'", "''") + "'"


@dataclass(frozen=True)
class DevInstallPlan:
    """Everything both scripts bake in, computed once from the served generation.

    :param plugin_name: The plugin's name, identical to the one the lab serves -- so the
        tool permission ids (``mcp__<plugin>_<server>__<tool>``) a developer writes against
        a local install are the ones a production install will use.
    :param version: The version being installed, shown to the user and carried by the
        archive it came from.
    :param archive_url: The lab URL the script downloads. Carries the version, so a stale
        script gets a 404 rather than the wrong bytes.
    :param marketplace_name: The name of the *local* marketplace the script writes.
    :param marketplace_json: The manifest the script writes, already serialized.
    :param posix_script_url: Where the bash script is served.
    :param windows_script_url: Where the PowerShell script is served.
    """

    plugin_name: str
    version: str
    archive_url: str
    marketplace_name: str
    marketplace_json: str
    posix_script_url: str
    windows_script_url: str

    @property
    def posix_command(self) -> str:
        """The one-liner to run on macOS, Linux or WSL."""
        return f"curl -fsSL {self.posix_script_url} | bash"

    @property
    def windows_command(self) -> str:
        """The one-liner to run in PowerShell."""
        return f"irm {self.windows_script_url} | iex"

    @property
    def install_command(self) -> str:
        """The Claude Code command that installs from the local marketplace."""
        return f"/plugin install {self.plugin_name}@{self.marketplace_name}"

    @property
    def update_command(self) -> str:
        """What to run after re-running the script, so Claude Code re-reads the folder."""
        return f"/plugin marketplace update {self.marketplace_name}"


def build_dev_install_plan(generated: GeneratedPlugin | None = None) -> DevInstallPlan:
    """Describe the local install of the generation this lab currently serves."""
    generated = generated or PluginGenerator.get_generated()
    marketplace_name = f"{generated.identity.marketplace_name}{DEV_MARKETPLACE_SUFFIX}"

    return DevInstallPlan(
        plugin_name=generated.identity.plugin_name,
        version=generated.version,
        archive_url=build_plugins_url(generated.archive_file_name),
        marketplace_name=marketplace_name,
        marketplace_json=json.dumps(
            build_dev_marketplace_manifest(generated, marketplace_name),
            indent=2,
            ensure_ascii=False,
        ),
        posix_script_url=build_plugins_url(POSIX_SCRIPT_FILE_NAME),
        windows_script_url=build_plugins_url(WINDOWS_SCRIPT_FILE_NAME),
    )


def build_dev_marketplace_manifest(
    generated: GeneratedPlugin, marketplace_name: str
) -> dict[str, Any]:
    """The local marketplace: the same plugin, sourced from a folder instead of a URL.

    No ``renames``: a marketplace created on a developer's machine has no history of served
    names to migrate, and a rename target must be a declared plugin.
    """
    entry = generated.marketplace_manifest["plugins"][0]

    return {
        "$schema": MARKETPLACE_SCHEMA_URL,
        "name": marketplace_name,
        "owner": {"name": generated.identity.lab_name},
        # Both scripts write the same manifest, so the description names neither of them.
        "description": (
            f"Local development copy of the Claude Code plugin served by the Constellab lab "
            f"'{generated.identity.lab_name}'. Installed from a folder; it does not update "
            f"itself."
        ),
        "plugins": [
            {
                "name": entry["name"],
                "description": entry["description"],
                "version": entry["version"],
                # The one source type with no scheme requirement. Relative to this file's
                # parent's parent -- the marketplace root the user adds.
                "source": f"./{generated.identity.plugin_name}",
            }
        ],
    }


def build_posix_script(plan: DevInstallPlan | None = None) -> str:
    """The bash script for macOS and Linux.

    Written against bash 3.2, which is what macOS still ships. Every external tool it needs
    has a fallback, because the three platforms disagree on what is installed by default:
    Ubuntu images often carry no ``unzip``, and a minimal container no ``curl``.
    """
    plan = plan or build_dev_install_plan()

    return f"""#!/usr/bin/env bash
# Installs the Claude Code plugin of the Constellab lab, from a local folder.
#
# Generated by the lab itself -- the plugin name, version and archive URL below are the
# ones it serves right now. Do not edit: re-download it instead, which is also how you
# pick up a new version.
#
# It writes under ~/{INSTALL_FOLDER}/ and, when the 'claude' CLI is on your PATH,
# registers the plugin with Claude Code. It starts nothing.
set -euo pipefail

PLUGIN_NAME={quote_for_bash(plan.plugin_name)}
PLUGIN_VERSION={quote_for_bash(plan.version)}
ARCHIVE_URL={quote_for_bash(plan.archive_url)}
MARKETPLACE_NAME={quote_for_bash(plan.marketplace_name)}

ROOT="${{CONSTELLAB_PLUGIN_DIR:-$HOME/{INSTALL_FOLDER}}}/$MARKETPLACE_NAME"
PLUGIN_DIR="$ROOT/$PLUGIN_NAME"

echo "Installing $PLUGIN_NAME $PLUGIN_VERSION"
echo "  from $ARCHIVE_URL"
echo "  into $PLUGIN_DIR"

download() {{
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL -o "$1" "$ARCHIVE_URL"
  elif command -v wget >/dev/null 2>&1; then
    wget -q -O "$1" "$ARCHIVE_URL"
  else
    echo "Neither curl nor wget is installed: cannot download the plugin." >&2
    return 1
  fi
}}

extract() {{
  if command -v unzip >/dev/null 2>&1; then
    unzip -q "$1" -d "$2"
  elif command -v python3 >/dev/null 2>&1; then
    python3 -m zipfile -e "$1" "$2"
  else
    echo "Neither unzip nor python3 is installed: cannot unpack the plugin." >&2
    return 1
  fi
}}

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

if ! download "$TMP_DIR/plugin.zip"; then
  echo >&2
  echo "The lab did not serve $ARCHIVE_URL." >&2
  echo "If the lab is running, it has moved on to another version: download this" >&2
  echo "script again to get the current one." >&2
  exit 1
fi

mkdir -p "$ROOT/.claude-plugin"
# Replaced whole rather than merged: a skill the lab no longer ships must not survive
# in the installed copy.
rm -rf "$PLUGIN_DIR"
mkdir -p "$PLUGIN_DIR"
extract "$TMP_DIR/plugin.zip" "$PLUGIN_DIR"

cat > "$ROOT/.claude-plugin/marketplace.json" <<'{JSON_TERMINATOR}'
{plan.marketplace_json}
{JSON_TERMINATOR}

# Registering the marketplace and installing the plugin are the same three CLI calls
# whether this is a first install or a re-run: all three are idempotent, and the update
# is what makes Claude Code re-read the folder this script just rewrote.
wire_up_claude_code() {{
  command -v claude >/dev/null 2>&1 || return 1
  claude plugin marketplace add "$ROOT" || return 1
  claude plugin marketplace update "$MARKETPLACE_NAME" || return 1
  claude plugin install "$PLUGIN_NAME@$MARKETPLACE_NAME" || return 1
}}

echo
if wire_up_claude_code; then
  echo "Done. Restart Claude Code to load $PLUGIN_NAME $PLUGIN_VERSION."
else
  echo "Downloaded, but the 'claude' CLI could not finish it, so do it by hand."
  echo "In Claude Code, in this order:"
  echo
  echo "  1. /plugin marketplace add $ROOT"
  echo "  2. {plan.install_command}"
  echo
  echo "Step 2 answers 'Marketplace not found' until step 1 has run."
fi
"""


def build_windows_script(plan: DevInstallPlan | None = None) -> str:
    """The PowerShell script for Windows.

    Uses only what Windows 10 ships (PowerShell 5.1): ``Invoke-WebRequest`` and
    ``Expand-Archive``. The manifest is written through ``UTF8Encoding($false)`` rather than
    ``Set-Content -Encoding UTF8``, which in 5.1 emits a BOM -- and a BOM ahead of ``{{`` is
    a JSON file some parsers reject.
    """
    plan = plan or build_dev_install_plan()
    install_folder = INSTALL_FOLDER.replace("/", "\\")

    return f"""#Requires -Version 5.1
# Installs the Claude Code plugin of the Constellab lab, from a local folder.
#
# Generated by the lab itself -- the plugin name, version and archive URL below are the
# ones it serves right now. Do not edit: re-download it instead, which is also how you
# pick up a new version.
#
# It writes under $HOME\\{install_folder}\\ and, when the 'claude' CLI is on your PATH,
# registers the plugin with Claude Code. It starts nothing.
$ErrorActionPreference = 'Stop'
# Invoke-WebRequest in 5.1 spends most of a small download drawing its progress bar.
$ProgressPreference = 'SilentlyContinue'

$PluginName = {quote_for_powershell(plan.plugin_name)}
$PluginVersion = {quote_for_powershell(plan.version)}
$ArchiveUrl = {quote_for_powershell(plan.archive_url)}
$MarketplaceName = {quote_for_powershell(plan.marketplace_name)}

# Assigned in steps rather than as one multi-line 'if' expression, which PowerShell 5.1
# parses differently depending on where the line breaks fall.
$Base = Join-Path $HOME '{install_folder}'
if ($env:USERPROFILE) {{ $Base = Join-Path $env:USERPROFILE '{install_folder}' }}
if ($env:CONSTELLAB_PLUGIN_DIR) {{ $Base = $env:CONSTELLAB_PLUGIN_DIR }}
$Root = Join-Path $Base $MarketplaceName
$PluginDir = Join-Path $Root $PluginName

Write-Host "Installing $PluginName $PluginVersion"
Write-Host "  from $ArchiveUrl"
Write-Host "  into $PluginDir"

$TmpDir = Join-Path ([System.IO.Path]::GetTempPath()) ([System.Guid]::NewGuid().ToString())
New-Item -ItemType Directory -Path $TmpDir -Force | Out-Null

try {{
    $Zip = Join-Path $TmpDir 'plugin.zip'

    try {{
        Invoke-WebRequest -Uri $ArchiveUrl -OutFile $Zip -UseBasicParsing
    }} catch {{
        # 'throw', not 'exit': this script is meant to be piped into Invoke-Expression,
        # where 'exit' would close the user's PowerShell session.
        throw ("The lab did not serve $ArchiveUrl. If the lab is running, it has moved " +
               "on to another version: download this script again to get the current one.")
    }}

    New-Item -ItemType Directory -Path (Join-Path $Root '.claude-plugin') -Force | Out-Null
    # Replaced whole rather than merged: a skill the lab no longer ships must not survive
    # in the installed copy.
    if (Test-Path $PluginDir) {{ Remove-Item -Recurse -Force $PluginDir }}
    New-Item -ItemType Directory -Path $PluginDir -Force | Out-Null
    Expand-Archive -Path $Zip -DestinationPath $PluginDir -Force

    $Manifest = @'
{plan.marketplace_json}
'@
    $ManifestPath = Join-Path $Root '.claude-plugin\\marketplace.json'
    [System.IO.File]::WriteAllText(
        $ManifestPath, $Manifest, (New-Object System.Text.UTF8Encoding($false)))
}} finally {{
    Remove-Item -Recurse -Force $TmpDir -ErrorAction SilentlyContinue
}}

# Registering the marketplace and installing the plugin are the same three CLI calls
# whether this is a first install or a re-run: all three are idempotent, and the update
# is what makes Claude Code re-read the folder this script just rewrote.
function Invoke-ClaudeCodeWiring {{
    if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {{ return $false }}

    # Every native call goes to the host explicitly: anything a function leaves on the
    # pipeline becomes part of its return value, and the CLI's own output would then read
    # as success whatever it exited with.
    try {{
        & claude plugin marketplace add $Root | Out-Host
        if ($LASTEXITCODE -ne 0) {{ return $false }}
        & claude plugin marketplace update $MarketplaceName | Out-Host
        if ($LASTEXITCODE -ne 0) {{ return $false }}
        & claude plugin install "$PluginName@$MarketplaceName" | Out-Host
        if ($LASTEXITCODE -ne 0) {{ return $false }}
    }} catch {{
        return $false
    }}

    return $true
}}

Write-Host ""
if (Invoke-ClaudeCodeWiring) {{
    Write-Host "Done. Restart Claude Code to load $PluginName $PluginVersion."
}} else {{
    Write-Host "Downloaded, but the 'claude' CLI could not finish it, so do it by hand."
    Write-Host "In Claude Code, in this order:"
    Write-Host ""
    Write-Host "  1. /plugin marketplace add $Root"
    Write-Host "  2. {plan.install_command}"
    Write-Host ""
    Write-Host "Step 2 answers 'Marketplace not found' until step 1 has run."
}}
"""

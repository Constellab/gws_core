"""The skills the bricks ship with their MCP tools.

A skill names the tools it drives. A tool renamed in a brick while its skill lived in
``gws_core`` would break nothing loudly -- the model would simply call a tool that does
not exist. So a brick ships both: its tools under ``src/``, its skills under
``<brick>/claude-plugin/skills/<name>/SKILL.md`` at the brick root.

That folder is outside ``src/``, which is fine: a brick is deployed as a folder (see
``SettingsLoader.load_brick``), and ``BrickInfo.path`` points at its root.

**The collected content is public**: it is served over an unauthenticated route, to
anyone who knows the lab's URL. A skill is documentation, so it must read like
documentation -- no customer names, no internal hostnames, no credentials.
"""

import json
import os
import re
from dataclasses import dataclass

from gws_core.brick.brick_helper import BrickHelper
from gws_core.core.utils.logger import Logger

# Where a brick keeps what it contributes to the lab's Claude Code plugin.
CLAUDE_PLUGIN_FOLDER_NAME = "claude-plugin"
SKILLS_FOLDER_NAME = "skills"
SKILL_FILE_NAME = "SKILL.md"

# The skills folder inside the generated archive. Each brick gets a sub-folder, so two
# bricks may ship a skill with the same folder name.
ARCHIVE_SKILLS_FOLDER = "skills"

_FRONTMATTER_DELIMITER = "---"
_DESCRIPTION_LINE = re.compile(r"^description:[ \t]*(.*)$", re.MULTILINE)

# Shortest a quoted scalar can be: the two quotes around an empty value.
_MIN_QUOTED_LENGTH = 2


@dataclass(frozen=True)
class PluginSkill:
    """One skill folder, read from a brick and ready to be written into the archive.

    :param brick_name: The brick that ships it.
    :param folder_name: The skill's folder name, as the brick wrote it.
    :param files: The folder's content, keyed by path relative to the skill folder
        (POSIX separators), ordered by path.
    """

    brick_name: str
    folder_name: str
    files: dict[str, bytes]

    @property
    def archive_path(self) -> str:
        """Where the skill lives in the archive, relative to the plugin root."""
        return f"{ARCHIVE_SKILLS_FOLDER}/{self.brick_name}/{self.folder_name}"

    @property
    def manifest_path(self) -> str:
        """How ``plugin.json`` refers to the skill."""
        return f"./{self.archive_path}"


def collect_skills(brick_names: list[str], lab_name: str) -> list[PluginSkill]:
    """Read the skills of the given bricks, with the lab's name injected in each.

    :param brick_names: Bricks to read, in the order their skills should appear.
    :param lab_name: The lab's name, injected into every skill description.
    """
    return [skill for brick_name in brick_names for skill in _collect_brick_skills(brick_name, lab_name)]


def _collect_brick_skills(brick_name: str, lab_name: str) -> list[PluginSkill]:
    """Read one brick's ``claude-plugin/skills/`` folder. Empty when it has none."""
    brick_info = BrickHelper.get_brick_info(brick_name)

    # No path in test mode for a brick that is not installed -- and nothing to read.
    if brick_info is None or not brick_info.path:
        return []

    skills_folder = os.path.join(brick_info.path, CLAUDE_PLUGIN_FOLDER_NAME, SKILLS_FOLDER_NAME)
    if not os.path.isdir(skills_folder):
        return []

    skills: list[PluginSkill] = []

    # Sorted, so the archive (and the version fingerprint derived from it) does not
    # depend on the order the file system happens to return.
    for folder_name in sorted(os.listdir(skills_folder)):
        skill_folder = os.path.join(skills_folder, folder_name)
        if not os.path.isdir(skill_folder):
            continue

        if not os.path.isfile(os.path.join(skill_folder, SKILL_FILE_NAME)):
            Logger.warning(
                f"Brick '{brick_name}' has a folder '{folder_name}' in its "
                f"{CLAUDE_PLUGIN_FOLDER_NAME}/{SKILLS_FOLDER_NAME} folder with no "
                f"{SKILL_FILE_NAME}. It is not a skill and is not served."
            )
            continue

        skills.append(
            PluginSkill(
                brick_name=brick_name,
                folder_name=folder_name,
                files=_read_skill_folder(skill_folder, brick_name, folder_name, lab_name),
            )
        )

    return skills


def _read_skill_folder(
    skill_folder: str, brick_name: str, folder_name: str, lab_name: str
) -> dict[str, bytes]:
    """Read every file of a skill folder, keyed by relative POSIX path."""
    files: dict[str, bytes] = {}

    for dir_path, dir_names, file_names in os.walk(skill_folder):
        dir_names.sort()
        for file_name in sorted(file_names):
            file_path = os.path.join(dir_path, file_name)
            relative_path = os.path.relpath(file_path, skill_folder).replace(os.sep, "/")

            with open(file_path, "rb") as file:
                content = file.read()

            if relative_path == SKILL_FILE_NAME:
                content = inject_lab_name(
                    content.decode("utf-8"), lab_name, f"{brick_name}/{folder_name}"
                ).encode("utf-8")

            files[relative_path] = content

    return dict(sorted(files.items()))


def inject_lab_name(skill_content: str, lab_name: str, skill_id: str) -> str:
    """Name the lab in a skill's description.

    A user with two labs installed sees two plugins shipping the same skill under the
    same description, and the description is what the model reads when it chooses. The
    lab's name goes first, because that is the part that tells the two apart.

    Only a single-line description can be rewritten (plain, or single- or
    double-quoted). Anything else is left alone with a warning: a skill that ships
    undescribed is better than one that ships with broken front matter.

    :param skill_content: The ``SKILL.md`` file, verbatim.
    :param lab_name: The lab's name.
    :param skill_id: How the skill is named in a warning, for its author.
    :return: The file with its description rewritten, or unchanged.
    """
    frontmatter_span = _find_frontmatter(skill_content)

    if frontmatter_span is None:
        Logger.warning(
            f"The skill '{skill_id}' has no YAML front matter, so the lab's name cannot be "
            "added to its description. Claude Code will not load it either."
        )
        return skill_content

    start, end = frontmatter_span
    match = _DESCRIPTION_LINE.search(skill_content, start, end)
    description = _read_scalar(match.group(1)) if match else None

    if match is None or description is None:
        Logger.warning(
            f"The skill '{skill_id}' has no single-line 'description' in its front matter, "
            "so the lab's name cannot be added to it. Two labs installed side by side will "
            "expose this skill with identical descriptions."
        )
        return skill_content

    # JSON strings are valid YAML double-quoted scalars, so a lab named with a quote or a
    # colon cannot break the front matter.
    new_line = "description: " + json.dumps(
        f"On the Constellab lab '{lab_name}': {description}", ensure_ascii=False
    )

    return skill_content[: match.start()] + new_line + skill_content[match.end() :]


def _find_frontmatter(skill_content: str) -> tuple[int, int] | None:
    """Return the bounds of the YAML front matter, delimiters excluded.

    Index-based rather than value-based, so a rewrite lands on the front matter and not
    on a later copy of the same text, whatever the file's line endings are.
    """
    delimiter = re.compile(rf"^[ \t]*{_FRONTMATTER_DELIMITER}[ \t]*$", re.MULTILINE)

    opening = delimiter.match(skill_content)
    if opening is None:
        return None

    closing = delimiter.search(skill_content, opening.end())
    if closing is None:
        return None

    return opening.end(), closing.start()


def _read_scalar(raw_value: str) -> str | None:
    """Read a single-line YAML scalar. ``None`` when it is empty or multi-line."""
    value = raw_value.strip()

    if not value or value.startswith(("|", ">", "&", "*")):
        return None

    if _is_quoted(value, '"'):
        try:
            return json.loads(value)
        except ValueError:
            return None

    if _is_quoted(value, "'"):
        return value[1:-1].replace("''", "'")

    return value


def _is_quoted(value: str, quote: str) -> bool:
    """Whether the value is wrapped in that quote -- a lone quote character is not."""
    return len(value) >= _MIN_QUOTED_LENGTH and value.startswith(quote) and value.endswith(quote)

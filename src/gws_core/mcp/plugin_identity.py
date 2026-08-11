"""Who this lab is, as a Claude Code marketplace and as a plugin.

Two names, generated from the lab's own identity, and only one of them may ever change:

===================  =================================  ==========
\\                    Derived from                       Changes?
===================  =================================  ==========
Marketplace ``name``  ``constellab-<lab id>``            **never**
Plugin ``name``       the lab's name                     follows it
===================  =================================  ==========

A renamed **marketplace** has no migration path -- every user would have to remove it
and add it again, from a URL they no longer have a reason to visit. A renamed
**plugin** migrates itself, through the ``renames`` map of the manifest. So the half
that is allowed to move is the half that can carry its users with it.

The names a lab has served are kept in ``Settings`` (the JSON file that already holds
``secret_key``), because ``renames`` has to list *every* previous name: a lab renamed
twice while a user was away must still migrate that user in one step.

Lose that file -- a recreated volume, a lab rebuilt from scratch -- and the history goes
with it: the manifest then carries no ``renames``, an install made under an older name
resolves to nothing, and those users reinstall from the same (unchanged) marketplace URL.
Nothing here detects that state, and nothing repairs it; a lab cannot know a name it no
longer remembers serving. Which is why saving is best-effort below rather than fatal --
the manifest served *now* is correct either way.
"""

from dataclasses import dataclass, field

from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.core.utils.string_helper import StringHelper

# Prefix of every Constellab marketplace name. The lab id follows it, so two labs never
# collide and one lab's marketplace name is the same string for its whole life.
MARKETPLACE_NAME_PREFIX = "constellab"

# What ``LAB_NAME`` defaults to when nobody named the lab (see ``Settings.get_lab_name``).
# Slugged, it is also the name every never-named lab would otherwise produce.
DEFAULT_PLUGIN_NAME = "lab"

# How much of the lab id goes into the names. Long enough that two labs of one user do
# not collide, short enough to stay readable in a permission rule.
LAB_ID_SUFFIX_LENGTH = 8

# Key under which the served plugin names are persisted, oldest first.
SETTINGS_SERVED_PLUGIN_NAMES_KEY = "claude_plugin_served_names"


@dataclass(frozen=True)
class PluginIdentity:
    """The names this lab serves, and the ones it served before.

    :param lab_name: The lab's human name, as configured (``LAB_NAME``).
    :param marketplace_name: The immutable marketplace name.
    :param plugin_name: The plugin name derived from the lab's current name.
    :param previous_plugin_names: Plugin names this lab served before, oldest first,
        excluding the current one.
    """

    lab_name: str
    marketplace_name: str
    plugin_name: str
    previous_plugin_names: list[str] = field(default_factory=list)

    def build_renames(self) -> dict[str, str]:
        """The manifest's ``renames`` map: every name once served -> the current one.

        Claude Code follows it when it cannot find a plugin under the name a user has
        installed, and migrates that user's settings to the new name. Emitting the whole
        history (rather than only the last name) is what makes two successive renames
        recoverable in one step.
        """
        return dict.fromkeys(self.previous_plugin_names, self.plugin_name)


def build_lab_id_suffix() -> str:
    """The lab-id characters that go into the marketplace name, and into an unnamed
    lab's plugin name."""
    return _slug(Settings.get_lab_id())[:LAB_ID_SUFFIX_LENGTH]


def build_marketplace_name() -> str:
    """The lab's marketplace name. Derived from the lab id, so it never changes."""
    return f"{MARKETPLACE_NAME_PREFIX}-{build_lab_id_suffix()}"


def build_plugin_name(lab_name: str) -> str:
    """The plugin name for a lab called ``lab_name``.

    A lab that was never named carries the default ``"Lab"`` (see
    ``Settings.get_lab_name``), so every unnamed lab would produce the plugin ``lab`` --
    and therefore *identical* tool permission ids on a machine that installed two of
    them, despite the marketplaces being distinct. Those labs get the id suffix too.
    """
    slug = _slug(lab_name)

    if not slug or slug == DEFAULT_PLUGIN_NAME:
        return f"{DEFAULT_PLUGIN_NAME}-{build_lab_id_suffix()}"

    return slug


def resolve_and_record_identity() -> PluginIdentity:
    """Resolve the lab's identity, recording the plugin name it is about to serve.

    Recording at generation, rather than at startup, is what keeps a lab that serves no
    plugin -- MCP off -- out of the history entirely. It errs the other way for a lab that
    does serve one: the generation also feeds the lab's own screen, so merely opening it
    records the name. Recording a name nobody installed costs one spare ``renames`` entry;
    failing to record one somebody did install costs that user their migration.
    """
    lab_name = Settings.get_lab_name()
    plugin_name = build_plugin_name(lab_name)
    served_names = _record_served_plugin_name(plugin_name)

    return PluginIdentity(
        lab_name=lab_name,
        marketplace_name=build_marketplace_name(),
        plugin_name=plugin_name,
        # A lab renamed back to a former name has that name twice in the history; it is
        # the current one, so it is not something to migrate away from.
        previous_plugin_names=[name for name in served_names if name != plugin_name],
    )


def get_served_plugin_names() -> list[str]:
    """The plugin names this lab has served, oldest first.

    Read defensively: this is a hand-editable JSON file, and an entry that is not a
    non-empty string would reach the manifest as a ``renames`` key Claude Code rejects,
    taking the whole marketplace down for every user of the lab -- to migrate an install
    that cannot exist, since no name this module builds is empty.
    """
    names = Settings.get_instance().data.get(SETTINGS_SERVED_PLUGIN_NAMES_KEY)

    if not isinstance(names, list):
        return []

    return [name for name in names if isinstance(name, str) and name]


def _record_served_plugin_name(plugin_name: str) -> list[str]:
    """Append the name to the served history when it differs from the last one.

    :return: The full history, oldest first, the given name included.
    """
    served_names = get_served_plugin_names()

    if served_names and served_names[-1] == plugin_name:
        return served_names

    served_names = [*served_names, plugin_name]

    settings = Settings.get_instance()
    settings.set_data(SETTINGS_SERVED_PLUGIN_NAMES_KEY, served_names)

    try:
        settings.save()
    except Exception as err:
        # Not fatal: the manifest served now is correct either way. What is lost is the
        # ability to migrate *this* rename later, which is the same degraded state as a
        # settings file recreated with the volume -- the user reinstalls the plugin.
        Logger.error(
            f"Could not persist the served Claude Code plugin name '{plugin_name}': {err}. "
            "A later rename of this lab will not migrate the plugin automatically."
        )

    return served_names


def _slug(text: str) -> str:
    """Lower-case, hyphen-separated form of a text, safe as a plugin name.

    Claude Code refuses a name containing a space and prefers kebab-case; the lowering is
    ours, so that renaming a lab from ``Mon Lab`` to ``mon lab`` does not read as a
    rename.
    """
    return StringHelper.slugify(text).lower()

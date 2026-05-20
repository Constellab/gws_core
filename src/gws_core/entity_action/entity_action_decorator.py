from collections.abc import Callable

from gws_core.brick.brick_helper import BrickHelper
from gws_core.core.utils.string_helper import StringHelper
from gws_core.entity_action.entity_action_plugin import EntityActionPlugin
from gws_core.entity_action.entity_action_registry import EntityActionRegistry


def entity_action_plugin(unique_name: str) -> Callable:
    """Decorator that registers an :class:`EntityActionPlugin` subclass.

    :param unique_name: identifier for the plugin. It must be unique within the
        brick that declares it: no two entity action plugins in the same brick
        can share the same ``unique_name``. It is automatically prefixed with
        the owning brick name (derived from the module path, like the typing
        system) to form a globally unique ``plugin_id`` of the form
        ``<brick_name>.<unique_name>``. That ``plugin_id`` namespaces every
        action name the plugin produces so the dispatch endpoint can route an
        action back to its owning plugin.

    The ``unique_name`` must be URL-safe: it can only contain alphanumeric
    characters and underscores (same rule as a task ``unique_name``). In
    particular it must not contain a dot, as the dot is the namespace
    separator.

    Example (declared in the gws_ai_toolkit brick)::

        @entity_action_plugin("analytics")
        class AnalyticsResourceActionPlugin(EntityActionPlugin):
            entity_action_type = EntityActionType.RESOURCE
            ...

        # registered plugin_id -> "gws_ai_toolkit.analytics"
    """

    def decorator(plugin_class: type[EntityActionPlugin]) -> type[EntityActionPlugin]:
        if not issubclass(plugin_class, EntityActionPlugin):
            raise Exception(
                f"The class '{plugin_class.__name__}' decorated with "
                f"@entity_action_plugin must extend EntityActionPlugin."
            )
        if getattr(plugin_class, "entity_action_type", None) is None:
            raise Exception(
                f"The entity action plugin '{plugin_class.__name__}' must set the "
                f"'entity_action_type' class attribute."
            )
        if not unique_name or not StringHelper.is_alphanumeric(unique_name):
            raise Exception(
                f"The entity action plugin name '{unique_name}' is not valid. It must "
                f"contain only alphanumeric characters and underscores ('_') so it is "
                f"safe to use in a URL."
            )

        # prefix with the brick name to make the plugin id globally unique
        brick_name = BrickHelper.get_brick_name(plugin_class)
        plugin_class.__plugin_name__ = unique_name
        plugin_class.__plugin_id__ = f"{brick_name}.{unique_name}"

        EntityActionRegistry.register(plugin_class)
        return plugin_class

    return decorator

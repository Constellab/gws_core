from collections.abc import Callable

from gws_core.brick.brick_helper import BrickHelper
from gws_core.entity_action.entity_action_plugin import EntityActionPlugin
from gws_core.entity_action.entity_action_registry import EntityActionRegistry


def entity_action_plugin(plugin_name: str) -> Callable:
    """Decorator that registers an :class:`EntityActionPlugin` subclass.

    :param plugin_name: identifier for the plugin, unique within the brick that
        declares it. It is automatically prefixed with the owning brick name
        (derived from the module path, like the typing system) to form a globally
        unique ``plugin_id`` of the form ``<brick_name>.<plugin_name>``. That
        ``plugin_id`` namespaces every action name the plugin produces so the
        dispatch endpoint can route an action back to its owning plugin.

    The ``plugin_name`` must not contain a dot, as the dot is the namespace
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
        if "." in plugin_name:
            raise Exception(
                f"The entity action plugin name '{plugin_name}' must not contain a "
                f"dot ('.'), it is the namespace separator."
            )

        # prefix with the brick name to make the plugin id globally unique
        brick_name = BrickHelper.get_brick_name(plugin_class)
        plugin_class.__plugin_name__ = plugin_name
        plugin_class.__plugin_id__ = f"{brick_name}.{plugin_name}"

        EntityActionRegistry.register(plugin_class)
        return plugin_class

    return decorator

from gws_core.entity_action.entity_action_plugin import EntityActionPlugin
from gws_core.entity_action.entity_action_type import EntityActionType


class EntityActionRegistry:
    """Global in-memory registry of :class:`EntityActionPlugin` instances.

    Populated at import time by the ``@entity_action_plugin`` decorator. It is
    indexed by entity type so listing actions for one entity only iterates the
    plugins targeting that entity type. Within an entity type, plugins are keyed
    by their globally unique ``plugin_id`` (``<brick_name>.<plugin_name>``).
    """

    # entity type -> (plugin_id -> plugin instance)
    _plugins: dict[EntityActionType, dict[str, EntityActionPlugin]] = {}

    @classmethod
    def register(cls, plugin_class: type[EntityActionPlugin]) -> None:
        """Instantiate and register a plugin class. Called by the decorator.

        Raises if a plugin with the same ``plugin_id`` is already registered,
        which means two plugins of the same brick share a name.
        """
        entity_type = plugin_class.entity_action_type
        plugin_id = plugin_class.__plugin_id__

        type_plugins = cls._plugins.setdefault(entity_type, {})
        if plugin_id in type_plugins:
            existing = type_plugins[plugin_id]
            raise Exception(
                f"2 entity action plugins register with the same id '{plugin_id}' "
                f"for entity type '{entity_type.value}'. "
                f"Already registered: {type(existing).__name__}. "
                f"Trying to register: {plugin_class.__name__}. "
                f"Please update the plugin name passed to @entity_action_plugin."
            )

        type_plugins[plugin_id] = plugin_class()

    @classmethod
    def get_plugins(cls, entity_type: EntityActionType) -> list[EntityActionPlugin]:
        """Return all plugins registered for the given entity type."""
        return list(cls._plugins.get(entity_type, {}).values())

    @classmethod
    def get_plugin(
        cls, entity_type: EntityActionType, plugin_id: str
    ) -> EntityActionPlugin | None:
        """Return the plugin with the given id for the entity type, or None."""
        return cls._plugins.get(entity_type, {}).get(plugin_id)

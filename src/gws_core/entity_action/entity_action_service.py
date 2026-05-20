from gws_core.core.exception.exceptions.bad_request_exception import (
    BadRequestException,
)
from gws_core.core.model.model import Model
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.string_helper import StringHelper
from gws_core.entity_action.entity_action import EntityAction, EntityActionKind
from gws_core.entity_action.entity_action_dto import (
    EntityActionMenuDTO,
    EntityActionResultDTO,
)
from gws_core.entity_action.entity_action_registry import EntityActionRegistry
from gws_core.entity_action.entity_action_type import EntityActionType


class EntityActionService:
    """Service that collects and dispatches entity action plugins."""

    @classmethod
    def get_entity_actions(
        cls, entity_type: EntityActionType, entity_id: str
    ) -> list[EntityActionMenuDTO]:
        """Return the action menu of an entity by asking every plugin of its type.

        Each plugin call is isolated: a faulty plugin is logged and skipped so it
        cannot break the whole menu.
        """
        entity = cls._get_entity(entity_type, entity_id)

        actions: list[EntityActionMenuDTO] = []
        for plugin in EntityActionRegistry.get_plugins(entity_type):
            try:
                for action in plugin.get_actions(entity):
                    cls._check_action_names(action, plugin.__plugin_id__)
                    actions.append(action.to_dto(plugin.__plugin_id__))
            except Exception as exception:
                Logger.error(
                    f"Entity action plugin '{plugin.__plugin_id__}' failed on "
                    f"{entity_type.value} '{entity_id}': {exception}"
                )
        return actions

    @classmethod
    def _check_action_names(cls, action: EntityAction, plugin_id: str) -> None:
        """Validate the ``action_name`` of a button action (and its children).

        The action name is namespaced and sent in the URL of the dispatch
        endpoint, so it must be URL-safe: only alphanumeric characters and
        underscores (same rule as a plugin name). A dot is forbidden because it
        is the namespace separator. Raises so the faulty plugin is logged and
        skipped by the caller.
        """
        if action.kind != EntityActionKind.BUTTON:
            return

        if not action.action_name or not StringHelper.is_alphanumeric(action.action_name):
            raise BadRequestException(
                f"The entity action name '{action.action_name}' of plugin "
                f"'{plugin_id}' is not valid. It must contain only alphanumeric "
                f"characters and underscores ('_') so it is safe to use in a URL."
            )

        for child in action.children or []:
            cls._check_action_names(child, plugin_id)

    @classmethod
    def execute_entity_action(
        cls, entity_type: EntityActionType, entity_id: str, action_name: str
    ) -> EntityActionResultDTO:
        """Dispatch an action to the plugin that owns it.

        ``action_name`` is namespaced as ``<plugin_id>.<local_name>`` where
        ``plugin_id`` is ``<brick_name>.<plugin_name>``. The local action name
        contains no dot, so the plugin id is everything before the last dot.
        """
        plugin_id, separator, local_name = action_name.rpartition(".")
        if not separator:
            raise BadRequestException(
                f"Invalid action name '{action_name}', expected "
                f"'<brick_name>.<plugin_name>.<action>'."
            )

        plugin = EntityActionRegistry.get_plugin(entity_type, plugin_id)
        if plugin is None:
            raise BadRequestException(
                f"No entity action plugin '{plugin_id}' registered for entity "
                f"type '{entity_type.value}'."
            )

        entity = cls._get_entity(entity_type, entity_id)
        return plugin.execute_action(entity, local_name)

    @classmethod
    def _get_entity(cls, entity_type: EntityActionType, entity_id: str) -> Model:
        """Load the entity model instance, raising if it does not exist."""
        model_type = entity_type.get_entity_model_type()
        return model_type.get_by_id_and_check(entity_id)

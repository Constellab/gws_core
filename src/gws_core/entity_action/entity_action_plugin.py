from abc import abstractmethod

from gws_core.core.model.model import Model
from gws_core.entity_action.entity_action import EntityAction
from gws_core.entity_action.entity_action_dto import EntityActionResultDTO
from gws_core.entity_action.entity_action_type import EntityActionType


class EntityActionPlugin:
    """Base class for a brick-contributed entity action provider.

    Subclass it, set :attr:`entity_action_type`, implement :meth:`get_actions`
    and :meth:`execute_action`, then decorate the subclass with
    ``@entity_action_plugin``. The subclass is instantiated once and registered
    in the global :class:`EntityActionRegistry`.

    Because a disabled brick's modules are never imported, its plugins are never
    registered: the conditional appearance of actions comes for free.
    """

    # set on the subclass by the developer: the single entity type this plugin
    # targets (e.g. EntityActionType.RESOURCE).
    entity_action_type: EntityActionType

    # set by the @entity_action_plugin decorator: the name passed to the
    # decorator, unique within the declaring brick.
    __plugin_name__: str

    # set by the @entity_action_plugin decorator: globally unique id of the form
    # '<brick_name>.<plugin_name>'. It namespaces every action name the plugin
    # produces so the dispatch endpoint can route an action back to its plugin.
    __plugin_id__: str

    @abstractmethod
    def get_actions(self, entity: Model) -> list[EntityAction]:
        """Return the actions to show for the given entity.

        ``entity`` is a model instance of :attr:`entity_action_type`. Return an
        empty list when no action applies.

        IMPORTANT: this is called for every plugin of the entity type on every
        ``GET /entity-action/{entity_type}/{id}`` request. It MUST be cheap -
        only in-memory checks on the already-loaded entity (type, flags, file
        extension). Do not load resource content, query the DB, or do I/O.
        """

    @abstractmethod
    def execute_action(self, entity: Model, action_name: str) -> EntityActionResultDTO:
        """Run the action identified by ``action_name``.

        ``action_name`` is the short, un-namespaced name (the dispatch endpoint
        strips the plugin namespace before calling this). May return a
        navigation instruction in the result.
        """

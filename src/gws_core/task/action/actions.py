# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from abc import abstractmethod
from typing import List, Type, TypedDict, final

from gws_core.brick.brick_service import BrickService
from gws_core.core.model.base import Base
from gws_core.core.utils.utils import Utils
from gws_core.model.typing_manager import TypingManager
from gws_core.model.typing_register_decorator import register_typing_class
from gws_core.resource.r_field.list_r_field import ListRField
from gws_core.resource.resource import Resource
from gws_core.resource.resource_decorator import resource_decorator


def action_decorator(unique_name: str,
                     human_name: str = "", short_description: str = ""):

    def decorator(action_class: Type['Action']):
        if not Utils.issubclass(action_class, Action):
            BrickService.log_brick_error(
                action_class,
                f"The action_decorator is used on the class: {action_class.__name__} and this class is not a sub class of Action")
            return action_class

        register_typing_class(action_class, "ACTION", unique_name=unique_name,
                              human_name=human_name, short_description=short_description)
        return action_class

    return decorator


class ActionDict(TypedDict):
    typing_name: str
    technical_name: str
    # human_name: str
    # short_description: str
    params: dict
    is_reversible: bool


class Action(Base):

    params: dict
    is_reversible: bool = True

    # Provided at the Class level automatically by the Decorator
    # //!\\ Do not modify theses values
    _typing_name: str = None
    _human_name: str = None
    _short_description: str = None

    def __init__(self, params: dict, is_reversible: bool = True) -> None:
        self.params = params
        self.is_reversible = is_reversible

    @abstractmethod
    def execute(self, resource: Resource) -> Resource:
        pass

    @abstractmethod
    def undo(self, resource: Resource) -> Resource:
        pass

    @final
    def export_config(self) -> ActionDict:
        return {
            "typing_name": self._typing_name,
            "params": self.params,
            "is_reversible": self.is_reversible
        }

    def get_short_description(self) -> str:
        return self._short_description

    @final
    def to_json(self) -> str:
        return {
            **self.export_config(),
            "human_name": self._human_name,
            'short_description': self.get_short_description()
        }


@resource_decorator("ActionsManager", hide=False, human_name="ActionsManager",
                    short_description="List of actions to modify a resource")
class ActionsManager(Resource):

    actions: List[ActionDict] = ListRField()

    def get_actions(self) -> List[Action]:
        actions: List[Action] = []

        for action_dict in self.actions:
            actions.append(self._instantiate_from_dict(action_dict))

        return actions

    def add_action(self, action: Action) -> None:
        self.actions.append(action.export_config())

    def pop_action(self) -> Action:
        if len(self.actions) == 0:
            raise Exception("No action to pop")
        action_dict = self.actions.pop()
        return self._instantiate_from_dict(action_dict)

    def _instantiate_from_dict(self, action_dict: ActionDict) -> Action:
        return self.instantiate_action(action_dict["typing_name"], action_dict["params"], action_dict["is_reversible"])

    @classmethod
    def instantiate_action(cls, action_typing_name: str, action_params: dict,
                           is_reversible: bool = True) -> Action:
        action_type: Type[Action] = TypingManager.get_type_from_name(action_typing_name)

        if action_type is None:
            raise Exception(f"Action with typing name '{action_typing_name}': not found")

        return action_type(action_params, is_reversible)

# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from abc import abstractmethod
from typing import Type, final

from typing_extensions import TypedDict

from gws_core.brick.brick_service import BrickService
from gws_core.core.model.base import Base
from gws_core.core.utils.utils import Utils
from gws_core.model.typing_register_decorator import register_typing_class
from gws_core.resource.resource import Resource


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

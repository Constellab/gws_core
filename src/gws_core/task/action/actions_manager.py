# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Type

from gws_core.model.typing_manager import TypingManager
from gws_core.resource.r_field.list_r_field import ListRField
from gws_core.resource.resource import Resource
from gws_core.resource.resource_decorator import resource_decorator

from .action import Action, ActionDict


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

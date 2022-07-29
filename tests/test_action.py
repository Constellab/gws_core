# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import List

from gws_core import Action, Resource, Table
from gws_core.experiment.experiment_enums import ExperimentType
from gws_core.impl.table.action.table_column_action import (AddColumnParam,
                                                            TableAddColumn)
from gws_core.resource.resource_model import ResourceModel, ResourceOrigin
from gws_core.task.action.action_service import ActionService
from gws_core.task.action.actions import ActionsManager, action_decorator
from gws_core.test.base_test_case import BaseTestCase
from pandas import DataFrame


@action_decorator("SimpleAction")
class SimpleAction(Action):
    def execute(self, resource: Resource) -> Resource:
        return resource

# test_action


class TestAction(BaseTestCase):

    def test_actions(self):

        action_manager: ActionsManager = ActionsManager()

        simple_action = SimpleAction({"param": "value"})
        action_manager.add_action(simple_action)

        actions: List[Action] = action_manager.get_actions()
        self.assertEqual(len(actions), 1)
        self.assertIsInstance(actions[0], SimpleAction)
        self.assertEqual(actions[0].params, {"param": "value"})

        action: Action = action_manager.pop_action()
        self.assertEqual(len(action_manager.get_actions()), 0)
        self.assertIsInstance(action, SimpleAction)
        self.assertEqual(action.params, {"param": "value"})

    async def test_action_service(self):

        df = DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        table = Table(df)

        resource_model = ResourceModel.save_from_resource(table, origin=ResourceOrigin.UPLOADED)

        # create the action experiment with empty list of actions
        result_model: ResourceModel = await ActionService.create_and_run_action_experiment(resource_model.id)

        # check the type of the generated resource
        self.assertEqual(result_model.origin, ResourceOrigin.ACTIONS)
        self.assertEqual(result_model.experiment.type, ExperimentType.ACTIONS)

        # chack that a new resource was created and its equal to the original one
        self.assertNotEqual(result_model.id, resource_model.id)
        result_resource: Table = result_model.get_resource()
        self.assertTrue(df.equals(result_resource.get_data()))

        # call the add column action
        params: AddColumnParam = {"name": "c", "index": 2}
        result_model = ActionService.add_action(result_model.id, TableAddColumn._typing_name, params)

        # check that the resource was updated
        result_resource: Table = result_model.get_resource()
        expected_df = DataFrame({"a": [1, 2, 3], "b": [4, 5, 6], "c": [None, None, None]})
        self.assertTrue(expected_df.equals(result_resource.get_data()))

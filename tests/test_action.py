# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import List

from gws_core import Action, Resource
from gws_core.experiment.experiment_enums import ExperimentType
from gws_core.impl.text.text import Text
from gws_core.resource.resource_model import ResourceModel, ResourceOrigin
from gws_core.task.action.action import action_decorator
from gws_core.task.action.action_service import ActionService
from gws_core.task.action.actions_manager import ActionsManager
from gws_core.test.base_test_case import BaseTestCase


@action_decorator("UpdateText")
class UpdateText(Action):

    def execute(self, resource: Text) -> Resource:
        self.params["old_text"] = resource.get_data()
        resource.set_data(self.params["new_text"])
        return resource

    def undo(self, resource: Text) -> Resource:
        resource.set_data(self.params["old_text"])
        return resource


# test_action
class TestAction(BaseTestCase):

    def test_actions(self):

        action_manager: ActionsManager = ActionsManager()

        simple_action = UpdateText({"new_text": "new_text"})
        action_manager.add_action(simple_action)

        actions: List[Action] = action_manager.get_actions()
        self.assertEqual(len(actions), 1)
        self.assertIsInstance(actions[0], UpdateText)
        self.assertEqual(actions[0].params, {"new_text": "new_text"})

        action: Action = action_manager.pop_action()
        self.assertEqual(len(action_manager.get_actions()), 0)
        self.assertIsInstance(action, UpdateText)
        self.assertEqual(action.params, {"new_text": "new_text"})

    def test_action_service(self):

        old_text = 'This is an old text'
        new_text = 'This is the new text'

        # create the resource to test
        text = Text(data=old_text)
        resource_model = ResourceModel.save_from_resource(text, origin=ResourceOrigin.UPLOADED)

        # create the action experiment with empty list of actions
        result_model: ResourceModel = ActionService.create_and_run_action_experiment(resource_model.id)

        # check the type of the generated resource
        self.assertEqual(result_model.origin, ResourceOrigin.ACTIONS)
        self.assertEqual(result_model.experiment.type, ExperimentType.ACTIONS)

        # check that a new resource was created and its equal to the original one
        self.assertNotEqual(result_model.id, resource_model.id)
        result_resource: Text = result_model.get_resource()
        self.assertEqual(result_resource.get_data(), old_text)

        # call the add column action
        params = {"new_text": new_text}
        result_model = ActionService.execute_action(result_model.id,
                                                    UpdateText._typing_name, params)

        # check that the resource was updated
        result_resource = result_model.get_resource()
        self.assertEqual(result_resource.get_data(), new_text)

        # check that the db resource was update
        result_model = ResourceModel.get_by_id(result_model.id)
        result_resource = result_model.get_resource()
        self.assertEqual(result_resource.get_data(), new_text)

        # undo the action
        result_model = ActionService.undo_last_action(result_model.id)
        result_resource = result_model.get_resource()
        self.assertEqual(result_resource.get_data(), old_text)

        # check that the db resource was updated
        result_model = ResourceModel.get_by_id(result_model.id)
        result_resource = result_model.get_resource()
        self.assertEqual(result_resource.get_data(), old_text)

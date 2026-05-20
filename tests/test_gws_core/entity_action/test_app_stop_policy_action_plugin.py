from gws_core import BaseTestCase
from gws_core.apps.app_dto import AppStopPolicy
from gws_core.apps.app_stop_policy_action_plugin import AppStopPolicyActionPlugin
from gws_core.apps.streamlit.streamlit_resource import StreamlitResource
from gws_core.entity_action.entity_action_dto import EntityActionButtonDTO
from gws_core.entity_action.entity_action_service import EntityActionService
from gws_core.entity_action.entity_action_type import EntityActionType
from gws_core.impl.robot.robot_resource import Robot
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_model import ResourceModel

_PLUGIN_ID = "gws_core.app_stop_policy"


# test_app_stop_policy_action_plugin
class TestAppStopPolicyActionPlugin(BaseTestCase):

    def _save_app(self, stop_policy: AppStopPolicy) -> ResourceModel:
        app = StreamlitResource()
        app.set_stop_policy(stop_policy)
        return ResourceModel.save_from_resource(app, origin=ResourceOrigin.UPLOADED)

    def test_button_for_auto_policy(self):
        # an app with AUTO policy -> button to disable auto-stop
        app_model = self._save_app(AppStopPolicy.AUTO)
        actions = EntityActionService.get_entity_actions(
            EntityActionType.RESOURCE, app_model.id
        )
        self.assertEqual(len(actions), 1)
        button = actions[0]
        self.assertIsInstance(button, EntityActionButtonDTO)
        self.assertEqual(button.text, "Disable auto-stop")
        self.assertEqual(
            button.action_name,
            f"{_PLUGIN_ID}.{AppStopPolicyActionPlugin.DISABLE_AUTO_STOP}",
        )

    def test_button_for_manual_policy(self):
        # an app with MANUAL policy -> button to enable auto-stop
        app_model = self._save_app(AppStopPolicy.MANUAL)
        actions = EntityActionService.get_entity_actions(
            EntityActionType.RESOURCE, app_model.id
        )
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0].text, "Enable auto-stop")

    def test_no_button_for_non_app_resource(self):
        # a non-app resource gets no stop-policy action
        robot_model = ResourceModel.save_from_resource(
            Robot.empty(), origin=ResourceOrigin.UPLOADED
        )
        actions = EntityActionService.get_entity_actions(
            EntityActionType.RESOURCE, robot_model.id
        )
        self.assertEqual(actions, [])

    def test_execute_action_toggles_policy(self):
        app_model = self._save_app(AppStopPolicy.AUTO)

        # disable auto-stop -> policy becomes MANUAL
        EntityActionService.execute_entity_action(
            EntityActionType.RESOURCE, app_model.id,
            f"{_PLUGIN_ID}.{AppStopPolicyActionPlugin.DISABLE_AUTO_STOP}",
        )
        reloaded = ResourceModel.get_by_id_and_check(app_model.id)
        self.assertEqual(reloaded.get_resource().get_stop_policy(), AppStopPolicy.MANUAL)

        # enable auto-stop -> policy becomes AUTO again
        EntityActionService.execute_entity_action(
            EntityActionType.RESOURCE, app_model.id,
            f"{_PLUGIN_ID}.{AppStopPolicyActionPlugin.ENABLE_AUTO_STOP}",
        )
        reloaded = ResourceModel.get_by_id_and_check(app_model.id)
        self.assertEqual(reloaded.get_resource().get_stop_policy(), AppStopPolicy.AUTO)

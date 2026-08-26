from typing import cast

from gws_core import BaseTestCase
from gws_core.apps.app_dto import AppStopPolicy
from gws_core.apps.app_resource_action_plugin import AppResourceActionPlugin
from gws_core.apps.streamlit.streamlit_resource import StreamlitResource
from gws_core.entity_action.entity_action_dto import EntityActionButtonDTO
from gws_core.entity_action.entity_action_service import EntityActionService
from gws_core.entity_action.entity_action_type import EntityActionType
from gws_core.impl.robot.robot_resource import Robot
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_model import ResourceModel

_PLUGIN_ID = "gws_core.app_resource"


# test_app_resource_action_plugin
class TestAppResourceActionPlugin(BaseTestCase):

    def _save_app(self, stop_policy: AppStopPolicy) -> ResourceModel:
        app = StreamlitResource()
        app.set_stop_policy(stop_policy)
        return ResourceModel.save_from_resource(app, origin=ResourceOrigin.UPLOADED)

    def test_button_for_auto_policy(self):
        # an app with AUTO policy -> button to disable auto-stop (+ custom subdomain button)
        app_model = self._save_app(AppStopPolicy.AUTO)
        actions = EntityActionService.get_entity_actions(
            EntityActionType.RESOURCE, app_model.id
        )
        self.assertEqual(len(actions), 2)
        button = actions[0]
        assert isinstance(button, EntityActionButtonDTO)
        self.assertEqual(button.text, "Disable auto-stop")
        self.assertEqual(
            button.action_name,
            f"{_PLUGIN_ID}.{AppResourceActionPlugin.DISABLE_AUTO_STOP}",
        )

    def test_button_for_manual_policy(self):
        # an app with MANUAL policy -> button to enable auto-stop (+ custom subdomain button)
        app_model = self._save_app(AppStopPolicy.MANUAL)
        actions = EntityActionService.get_entity_actions(
            EntityActionType.RESOURCE, app_model.id
        )
        self.assertEqual(len(actions), 2)
        self.assertEqual(actions[0].text, "Enable auto-stop")

    def test_custom_subdomain_button(self):
        # every app exposes a custom-subdomain button with a single-field config form,
        # pre-filled with the app's current subdomain
        app = StreamlitResource()
        app.set_custom_subdomain("my-app")
        app_model = ResourceModel.save_from_resource(app, origin=ResourceOrigin.UPLOADED)

        actions = EntityActionService.get_entity_actions(
            EntityActionType.RESOURCE, app_model.id
        )
        subdomain_button = actions[1]
        assert isinstance(subdomain_button, EntityActionButtonDTO)
        self.assertEqual(subdomain_button.text, "Set custom subdomain")
        self.assertEqual(
            subdomain_button.action_name,
            f"{_PLUGIN_ID}.{AppResourceActionPlugin.SET_CUSTOM_SUBDOMAIN}",
        )
        # the form carries the current subdomain as the field default value
        assert subdomain_button.config_specs is not None
        subdomain_spec = subdomain_button.config_specs[
            AppResourceActionPlugin.SUBDOMAIN_PARAM
        ]
        self.assertEqual(subdomain_spec.default_value, "my-app")

    def test_execute_set_and_clear_custom_subdomain(self):
        app_model = self._save_app(AppStopPolicy.MANUAL)

        # set the custom subdomain from the submitted form values
        EntityActionService.execute_entity_action(
            EntityActionType.RESOURCE, app_model.id,
            f"{_PLUGIN_ID}.{AppResourceActionPlugin.SET_CUSTOM_SUBDOMAIN}",
            {AppResourceActionPlugin.SUBDOMAIN_PARAM: "my-executed-app"},
        )
        reloaded = ResourceModel.get_by_id_and_check(app_model.id)
        reloaded_app = cast(StreamlitResource, reloaded.get_resource())
        self.assertEqual(reloaded_app.get_custom_subdomain(), "my-executed-app")

        # an empty value clears the subdomain
        EntityActionService.execute_entity_action(
            EntityActionType.RESOURCE, app_model.id,
            f"{_PLUGIN_ID}.{AppResourceActionPlugin.SET_CUSTOM_SUBDOMAIN}",
            {AppResourceActionPlugin.SUBDOMAIN_PARAM: ""},
        )
        reloaded = ResourceModel.get_by_id_and_check(app_model.id)
        reloaded_app = cast(StreamlitResource, reloaded.get_resource())
        self.assertIsNone(reloaded_app.get_custom_subdomain())

    def test_no_button_for_non_app_resource(self):
        # a non-app resource gets no action
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
            f"{_PLUGIN_ID}.{AppResourceActionPlugin.DISABLE_AUTO_STOP}",
        )
        reloaded = ResourceModel.get_by_id_and_check(app_model.id)
        reloaded_app = cast(StreamlitResource, reloaded.get_resource())
        self.assertEqual(reloaded_app.get_stop_policy(), AppStopPolicy.MANUAL)

        # enable auto-stop -> policy becomes AUTO again
        EntityActionService.execute_entity_action(
            EntityActionType.RESOURCE, app_model.id,
            f"{_PLUGIN_ID}.{AppResourceActionPlugin.ENABLE_AUTO_STOP}",
        )
        reloaded = ResourceModel.get_by_id_and_check(app_model.id)
        reloaded_app = cast(StreamlitResource, reloaded.get_resource())
        self.assertEqual(reloaded_app.get_stop_policy(), AppStopPolicy.AUTO)

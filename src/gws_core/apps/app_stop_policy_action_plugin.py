from gws_core.apps.app_dto import AppStopPolicy
from gws_core.apps.app_resource import AppResource
from gws_core.apps.apps_manager import AppsManager
from gws_core.entity_action.entity_action import EntityAction
from gws_core.entity_action.entity_action_decorator import entity_action_plugin
from gws_core.entity_action.entity_action_dto import EntityActionResultDTO
from gws_core.entity_action.entity_action_plugin import EntityActionPlugin
from gws_core.entity_action.entity_action_type import EntityActionType
from gws_core.resource.resource_model import ResourceModel


@entity_action_plugin("app_stop_policy")
class AppStopPolicyActionPlugin(EntityActionPlugin):
    """Adds a button to enable/disable the auto-stop of an app resource.

    With the AUTO stop policy an app is automatically stopped when no connection
    is detected; with MANUAL it stays running. The button toggles between the
    two and only appears on :class:`AppResource` resources.
    """

    entity_action_type = EntityActionType.RESOURCE

    # local action names (namespaced with the plugin id when sent to the front)
    ENABLE_AUTO_STOP = "enable_auto_stop"
    DISABLE_AUTO_STOP = "disable_auto_stop"

    def get_actions(self, entity: ResourceModel) -> list[EntityAction]:
        # cheap check: only app resources have a stop policy
        if not entity.is_application():
            return []

        app_resource = entity.get_resource()
        if not isinstance(app_resource, AppResource):
            return []

        if app_resource.get_stop_policy() == AppStopPolicy.AUTO:
            # auto-stop is on -> offer to disable it
            return [
                EntityAction.button(
                    action_name=self.DISABLE_AUTO_STOP,
                    text="Disable auto-stop",
                    icon="motion_photos_paused",
                )
            ]

        # auto-stop is off (MANUAL) -> offer to enable it
        return [
            EntityAction.button(
                action_name=self.ENABLE_AUTO_STOP,
                text="Enable auto-stop",
                icon="motion_photos_auto",
            )
        ]

    def execute_action(self, entity: ResourceModel,
                       action_name: str) -> EntityActionResultDTO:
        if action_name == self.DISABLE_AUTO_STOP:
            stop_policy = AppStopPolicy.MANUAL
            message = "Auto-stop disabled, the app will stay running."
        elif action_name == self.ENABLE_AUTO_STOP:
            stop_policy = AppStopPolicy.AUTO
            message = "Auto-stop enabled, the app will stop when unused."
        else:
            raise Exception(f"Unknown app stop policy action '{action_name}'")

        AppsManager.set_stop_policy(entity.id, stop_policy)
        return EntityActionResultDTO(message=message)

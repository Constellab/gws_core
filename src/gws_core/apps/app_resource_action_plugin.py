from gws_core.apps.app_dto import AppStopPolicy
from gws_core.apps.app_resource import AppResource
from gws_core.apps.apps_manager import AppsManager
from gws_core.config.config_params import ConfigParamsDict
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.entity_action.entity_action import EntityAction
from gws_core.entity_action.entity_action_decorator import entity_action_plugin
from gws_core.entity_action.entity_action_dto import EntityActionResultDTO
from gws_core.entity_action.entity_action_plugin import EntityActionPlugin
from gws_core.entity_action.entity_action_type import EntityActionType
from gws_core.resource.resource_model import ResourceModel


@entity_action_plugin("app_resource")
class AppResourceActionPlugin(EntityActionPlugin):
    """Adds management buttons to an :class:`AppResource`: enable/disable auto-stop and
    set its custom subdomain.

    With the AUTO stop policy an app is automatically stopped when no connection
    is detected; with MANUAL it stays running. The auto-stop button toggles between
    the two. The custom-subdomain button opens a form to set (or clear) the app's
    stable host alias. All actions only appear on :class:`AppResource` resources.
    """

    entity_action_type = EntityActionType.RESOURCE

    # local action names (namespaced with the plugin id when sent to the front)
    ENABLE_AUTO_STOP = "enable_auto_stop"
    DISABLE_AUTO_STOP = "disable_auto_stop"
    SET_CUSTOM_SUBDOMAIN = "set_custom_subdomain"

    # form field key of the custom subdomain input
    SUBDOMAIN_PARAM = "subdomain"

    def get_actions(self, entity: ResourceModel) -> list[EntityAction]:
        # cheap check: only app resources have a stop policy
        if not entity.is_application():
            return []

        app_resource = entity.get_resource()
        if not isinstance(app_resource, AppResource):
            return []

        if app_resource.get_stop_policy() == AppStopPolicy.AUTO:
            # auto-stop is on -> offer to disable it
            stop_policy_action = EntityAction.button(
                action_name=self.DISABLE_AUTO_STOP,
                text="Disable auto-stop",
                icon="motion_photos_paused",
            )
        else:
            # auto-stop is off (MANUAL) -> offer to enable it
            stop_policy_action = EntityAction.button(
                action_name=self.ENABLE_AUTO_STOP,
                text="Enable auto-stop",
                icon="motion_photos_auto",
            )

        return [stop_policy_action, self._build_custom_subdomain_action(app_resource)]

    def _build_custom_subdomain_action(self, app_resource: AppResource) -> EntityAction:
        """Build the button that opens the custom-subdomain form.

        The form has a single optional text field pre-filled with the app's current
        subdomain. Submitting an empty value clears the subdomain.
        """
        return EntityAction.button(
            action_name=self.SET_CUSTOM_SUBDOMAIN,
            text="Set custom subdomain",
            icon="dns",
            config_specs=ConfigSpecs(
                {
                    self.SUBDOMAIN_PARAM: StrParam(
                        default_value=app_resource.get_custom_subdomain(),
                        optional=True,
                        human_name="Custom subdomain",
                        short_description=(
                            "A stable host alias for the app (a single DNS label, e.g. "
                            "'my-app'). Leave empty to clear it and restore the default host."
                        ),
                        regex=r"[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?",
                        regex_description=(
                            "Use lowercase letters, digits and hyphens only, and start and "
                            "end with a letter or digit (e.g. 'my-app')"
                        ),
                    )
                }
            ),
        )

    def execute_action(
        self, entity: ResourceModel, action_name: str, config_params: ConfigParamsDict
    ) -> EntityActionResultDTO:
        if action_name == self.DISABLE_AUTO_STOP:
            stop_policy = AppStopPolicy.MANUAL
            message = "Auto-stop disabled, the app will stay running."
        elif action_name == self.ENABLE_AUTO_STOP:
            stop_policy = AppStopPolicy.AUTO
            message = "Auto-stop enabled, the app will stop when unused."
        elif action_name == self.SET_CUSTOM_SUBDOMAIN:
            return self._execute_set_custom_subdomain(entity, config_params)
        else:
            raise Exception(f"Unknown app resource action '{action_name}'")

        AppsManager.set_stop_policy(entity.id, stop_policy)
        return EntityActionResultDTO(message=message)

    def _execute_set_custom_subdomain(
        self, entity: ResourceModel, config_params: ConfigParamsDict
    ) -> EntityActionResultDTO:
        """Set or clear the app's custom subdomain from the submitted form values."""
        subdomain = config_params.get(self.SUBDOMAIN_PARAM)

        # AppsManager.set_custom_subdomain validates, checks uniqueness, persists and
        # applies the change live; a falsy value clears the subdomain.
        AppsManager.set_custom_subdomain(entity.id, subdomain)

        if subdomain:
            message = f"Custom subdomain set to '{subdomain}'."
        else:
            message = "Custom subdomain cleared, the default host is restored."
        return EntityActionResultDTO(message=message)

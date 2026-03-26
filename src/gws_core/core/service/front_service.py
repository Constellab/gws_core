from typing import Literal

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings


class FrontTheme(BaseModelDTO):
    """Class that represent the theme of the front application

    :param BaseModelDTO: _description_
    :type BaseModelDTO: _type_
    """

    theme: Literal["light", "dark"]

    # background color of the application
    background_color: str

    # background color of cards
    secondary_background_color: str

    # color for border, outline, hover, etc.
    outline_color: str

    # text color used for the text on the background_color and secondary_background_color
    text_color: str

    # primary color used for the main color of the application
    primary_color: str
    # primary contrast color used for the text on the primary color
    primary_contrast_color: str

    # accent color used for the element to accentuate
    accent_color: str
    # accent contrast color used for the text on the accent color
    accent_contrast_color: str

    # warn color used for the element to warn (like error, warnings)
    warn_color: str
    # warn contrast color used for the text on the warn color
    warn_contrast_color: str


class FrontService:
    _lab_url: str

    def __init__(self, lab_url: str | None = None) -> None:
        if lab_url is not None:
            self._lab_url = lab_url
        else:
            self._lab_url = Settings.get_front_url()

    def get_scenarios_list_url(self) -> str:
        return self.get_app_url() + "/scenario"

    def get_scenario_url(self, scenario_id: str) -> str:
        return self.get_scenarios_list_url() + "/" + scenario_id

    def get_resources_list_url(self) -> str:
        return self.get_app_url() + "/resource"

    def get_resource_url(self, resource_id: str) -> str:
        return self.get_resources_list_url() + "/" + resource_id

    def get_views_list_url(self) -> str:
        return self.get_app_url() + "/view"

    def get_view_url(self, view_id: str) -> str:
        return self.get_views_list_url() + "/" + view_id

    def get_scenario_templates_list_url(self) -> str:
        return self.get_app_url() + "/scenario-template"

    def get_scenario_template_url(self, template_id: str) -> str:
        return self.get_scenario_templates_list_url() + "/" + template_id

    ############################################### NOTE ###############################################

    def get_notes_list_url(self) -> str:
        return self.get_app_url() + "/note"

    def get_note_url(self, note_id: str) -> str:
        return self.get_notes_list_url() + "/" + note_id

    def get_note_templates_list_url(self) -> str:
        return self.get_app_url() + "/note-template"

    def get_note_template_url(self, template_id: str) -> str:
        return self.get_note_templates_list_url() + "/" + template_id

    ############################################### MONITORING ###############################################

    def get_monitoring_dashboard_url(self) -> str:
        return self.get_app_url() + "/monitoring"

    def get_monitoring_lab_url(self) -> str:
        return self.get_monitoring_dashboard_url() + "/usage"

    def get_monitoring_tags_url(self) -> str:
        return self.get_monitoring_dashboard_url() + "/tags"

    def get_monitoring_virtual_envs_url(self) -> str:
        return self.get_monitoring_dashboard_url() + "/virtual-envs"

    def get_monitoring_logs_url(self) -> str:
        return self.get_monitoring_dashboard_url() + "/logs"

    def get_monitoring_credentials_url(self) -> str:
        return self.get_monitoring_dashboard_url() + "/credentials"

    def get_monitoring_activity_url(self) -> str:
        return self.get_monitoring_dashboard_url() + "/activity"

    def get_monitoring_other_url(self) -> str:
        return self.get_monitoring_dashboard_url() + "/other"

    ############################################### OPEN URLS ###############################################

    def get_app_open_url(self) -> str:
        return self._lab_url + "/open"

    def get_resource_open_url(self, token: str) -> str:
        return self.get_app_open_url() + "/resource/" + token

    def get_resource_open_space_url(self, token: str, user_access_token: str) -> str:
        """Open route to access the resource but the user needs to be authenticated
        via the user_access_token
        """
        return (
            self.get_resource_open_url(token)
            + "?gws_user_access_token="
            + user_access_token
            + "&hide_header=true"
        )

    ############################################### OTHER URLS ###############################################

    def get_auto_login_url(self, expires_in: int) -> str:
        return self._lab_url + "/auto-login?expiresIn=" + str(expires_in)

    def get_app_url(self) -> str:
        return self._lab_url + "/app"

    def get_front_url(self) -> str:
        return self._lab_url

    ############################################### STATIC THEME METHODS ###############################################

    @staticmethod
    def get_light_theme() -> FrontTheme:
        return FrontTheme(
            theme="light",
            background_color="#FFFFFF",
            secondary_background_color="#EAEAEA",
            outline_color="#d2d2d2",
            text_color="#181c1c",
            primary_color="#49A8A9",
            primary_contrast_color="#222222",
            accent_color="#6C4EF6",
            accent_contrast_color="#FFFFFF",
            warn_color="#F991C3",
            warn_contrast_color="#222222",
        )

    @staticmethod
    def get_dark_theme() -> FrontTheme:
        return FrontTheme(
            theme="dark",
            background_color="#222222",
            secondary_background_color="#2B2D2E",
            outline_color="#494949",
            text_color="#dfe3e3",
            primary_color="#49A8A9",
            primary_contrast_color="#222222",
            accent_color="#6C4EF6",
            accent_contrast_color="#FFFFFF",
            warn_color="#F991C3",
            warn_contrast_color="#222222",
        )

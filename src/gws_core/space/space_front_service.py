

from typing import Literal

from gws_core.core.utils.settings import Settings


class SpaceFrontService:
    """ Service to get the URL of Space app.
    """

    space_base_url: str

    def __init__(self, space_base_url: str = None):
        """Initialize the SpaceFrontService with an optional base URL.

        :param space_base_url: The base URL of the Space app. If not provided, it will use the default from settings.
        :type space_base_url: str, optional
        """
        if space_base_url:
            self.space_base_url = space_base_url
        else:
            self.space_base_url = Settings.get_space_front_url()

    def get_folder_url(self, folder_id: str) -> str:
        """Get the URL of a specific folder of the Space app."""
        return f"{self.get_app_url()}/folder/{folder_id}"

    def get_document_url(self, document_id: str) -> str:
        """Get the URL of a specific document of the Space app."""
        return f"{self.get_app_url()}/folder/document/{document_id}/preview"

    def get_note_url(self, note_id: str) -> str:
        """Get the URL of the notes in a specific folder of the Space app."""
        return f"{self.get_app_url()}/folder/document/{note_id}"

    def get_lab_note_url(self, lab_note_id: str) -> str:
        """Get the URL of the lab note in a specific folder of the Space app."""
        return f"{self.get_app_url()}/folder/note/{lab_note_id}"

    def get_scenario_url(self, scenario_id: str) -> str:
        """Get the URL of a specific scenario of the Space app."""
        return f"{self.get_app_url()}/folder/scenario/{scenario_id}"

    def get_resource_url(self, resource_id: str) -> str:
        """Get the URL of a specific resource of the Space app."""
        return f"{self.get_app_url()}/folder/resource/{resource_id}"

    def get_folder_chat_url(self, folder_id: str) -> str:
        """Get the URL of the chat for a specific folder of the Space app."""
        return f"{self.get_app_url()}/chat/folder/{folder_id}"

    ################################### LAB ###################################

    def get_lab_url(
            self, lab_id: str, tab: Literal['dashboard', 'config', 'usage', 'backup', 'status-history'] = None) -> str:
        """Get the URL of a specific lab of the Space app."""
        return f"{self.get_app_url()}/labs/{lab_id}" + (f"/{tab}" if tab else '')

    def get_current_lab_url(
            self, tab: Literal['dashboard', 'config', 'usage', 'backup', 'status-history'] = None) -> str:
        """Get the URL of the current lab of the Space app."""
        lab_id = Settings.get_lab_id()
        return self.get_lab_url(lab_id, tab)

    ################################### OTHERS ###################################

    def get_team_url(self, team_id: str) -> str:
        """Get the URL of a specific team of the Space app."""
        return f"{self.get_app_url()}/structure/team/{team_id}"

    def get_home_url(self) -> str:
        """Get the URL of the home of the Space app."""
        return f"{self.get_app_url()}/home"

    def get_app_url(self) -> str:
        """Get the base URL of the Space front service."""
        return self.get_url() + '/app'

    def get_url(self) -> str:
        """Get the URL of the Space front service."""
        return self.space_base_url

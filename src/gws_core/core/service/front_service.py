

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.utils.settings import Settings


class FrontTheme(BaseModelDTO):
    """Class that represent the theme of the front application

    :param BaseModelDTO: _description_
    :type BaseModelDTO: _type_
    """

    background_color: str
    secondary_background_color: str

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


class FrontService():

    @staticmethod
    def get_scenario_url(scenario_id: str) -> str:
        return FrontService.get_app_url() + '/scenario/' + scenario_id

    @staticmethod
    def get_note_url(note_id: str) -> str:
        return FrontService.get_app_url() + '/note/' + note_id

    @staticmethod
    def get_resource_url(resource_id: str) -> str:
        return FrontService.get_app_url() + '/resource/' + resource_id

    @staticmethod
    def get_view_url(view_id: str) -> str:
        return FrontService.get_app_url() + '/view/' + view_id

    @staticmethod
    def get_auto_login_url(expires_in: int) -> str:
        return Settings.get_front_url() + '/auto-login?expiresIn=' + str(expires_in)

    @staticmethod
    def get_app_url() -> str:
        return Settings.get_front_url() + '/app'

    @staticmethod
    def get_front_url() -> str:
        return Settings.get_front_url()

    @staticmethod
    def get_light_theme() -> FrontTheme:
        return FrontTheme(
            background_color='#FFFFFF',
            secondary_background_color='#EAEAEA',
            text_color='#222222',
            primary_color='#49A8A9',
            primary_contrast_color='#222222',
            accent_color='#6C4EF6',
            accent_contrast_color='#FFFFFF',
            warn_color='#F991C3',
            warn_contrast_color='#222222'
        )

    @staticmethod
    def get_dark_theme() -> FrontTheme:
        return FrontTheme(
            background_color='#222222',
            secondary_background_color='#2B2D2E',
            text_color='#FFFFFF',
            primary_color='#49A8A9',
            primary_contrast_color='#222222',
            accent_color='#6C4EF6',
            accent_contrast_color='#FFFFFF',
            warn_color='#F991C3',
            warn_contrast_color='#222222'
        )

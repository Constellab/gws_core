# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from enum import Enum
from typing import Optional

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.utils.logger import Logger


class TypingIconType(Enum):
    MATERIAL_ICON = "MATERIAL_ICON"
    COMMUNITY_ICON = "COMMUNITY_ICON"
    COMMUNITY_IMAGE = "COMMUNITY_IMAGE"


class TypingIconColor(Enum):
    WHITE = "#FFFFFF"
    BLACK = "#000000"


class TypingStyle(BaseModelDTO):

    icon_technical_name: str = None
    icon_type: TypingIconType = None
    background_color: Optional[str] = None
    icon_color: Optional[TypingIconColor] = None

    def fill_empty_values(self) -> None:
        """Method to fill the background color and icon color if they are not set.
        """
        if self.icon_type == TypingIconType.COMMUNITY_IMAGE:
            if self.background_color is None:
                self.background_color = "#FFFFFF"
        else:
            if self.background_color is None:
                self.background_color = "#af3e01"
        if self.icon_color is None:
            self.icon_color = self.get_contrast_color(self.background_color)

    def copy_from_style(self, style: 'TypingStyle') -> None:
        if not self.background_color and not self.icon_color:
            self.background_color = style.background_color
            self.icon_color = style.icon_color

    @staticmethod
    def material_icon(material_icon_name: str, background_color: str = None,
                      icon_color: Optional[TypingIconColor] = None) -> 'TypingStyle':
        """ Use an icon from the material icon library. List of available icons are here :
        https://fonts.google.com/icons?icon.set=Material+Icons

        :param icon_technical_name: name of the material icon
        :type icon_technical_name: str
        :param background_color: background color of the typing as hex color code, defaults to None
        :type background_color: str, optional
        :param icon_color: icon color (black or white) when displayed over the background color, defaults to None
        :type icon_color: Optional[TypingIconColor], optional
        :return: TypingStyle object
        :rtype: TypingStyle
        """
        return TypingStyle(icon_technical_name=material_icon_name,
                           icon_type=TypingIconType.MATERIAL_ICON,
                           background_color=TypingStyle.check_background_color(background_color),
                           icon_color=TypingStyle.check_icon_color(icon_color)
                           )

    @staticmethod
    def community_icon(icon_technical_name: str, background_color: str = None,
                       icon_color: Optional[TypingIconColor] = None) -> 'TypingStyle':
        """ Use an icon from the community icon library. List of available icons are here :
        https://constellab.community/icons

        :param icon_technical_name: technical name of the icon
        :type icon_technical_name: str
        :param background_color: background color of the typing as hex color code, defaults to None
        :type background_color: str, optional
        :param icon_color: icon color (black or white) when displayed over the background color, defaults to None
        :type icon_color: Optional[TypingIconColor], optional
        :return: _description_
        :rtype: TypingStyle
        """
        return TypingStyle(icon_technical_name=icon_technical_name,
                           icon_type=TypingIconType.COMMUNITY_ICON,
                           background_color=TypingStyle.check_background_color(background_color),
                           icon_color=TypingStyle.check_icon_color(icon_color)
                           )

    @staticmethod
    def community_image(icon_technical_name: str, background_color: str = None) -> 'TypingStyle':
        """ Use an image from the community image library. List of available images are here :
        https://constellab.community/icons

        :param icon_technical_name: technical name of the image
        :type icon_technical_name: str
        :param background_color: background color of the typing, defaults to None
        :type background_color: str, optional
        :return: _description_
        :rtype: TypingStyle
        """
        return TypingStyle(icon_technical_name=icon_technical_name,
                           icon_type=TypingIconType.COMMUNITY_IMAGE,
                           background_color=TypingStyle.check_background_color(background_color),
                           icon_color=None)

    @staticmethod
    def default_resource() -> 'TypingStyle':
        return TypingStyle(icon_technical_name="resource",
                           icon_type=TypingIconType.MATERIAL_ICON,
                           background_color="#af3e01",
                           icon_color=TypingIconColor.WHITE)

    @staticmethod
    def default_task() -> 'TypingStyle':
        return TypingStyle(icon_technical_name="process",
                           icon_type=TypingIconType.MATERIAL_ICON,
                           background_color="#af3e01",
                           icon_color=TypingIconColor.WHITE)

    @staticmethod
    def default_protocol() -> 'TypingStyle':
        return TypingStyle(icon_technical_name="protocol",
                           icon_type=TypingIconType.MATERIAL_ICON,
                           background_color="#af3e01",
                           icon_color=TypingIconColor.WHITE)

    @staticmethod
    def default_view() -> 'TypingStyle':
        return TypingStyle(icon_technical_name="assessment",
                           icon_type=TypingIconType.MATERIAL_ICON,
                           background_color="#af3e01",
                           icon_color=TypingIconColor.WHITE)

    @staticmethod
    def check_background_color(background_color: str) -> str:
        if background_color and (not background_color.startswith("#") or len(background_color) != 7):
            Logger.error(f"Invalid background color '{background_color}'. Must be a hex color code")
            return None
        return background_color

    @staticmethod
    def check_icon_color(icon_color: str) -> TypingIconColor:
        if icon_color and not isinstance(icon_color, TypingIconColor):
            Logger.error(f"Invalid icon color '{icon_color}'. Must be a TypingIconColor")
            return None
        return icon_color

    @staticmethod
    def get_contrast_color(color: str) -> TypingIconColor:
        if color is None:
            return TypingIconColor.WHITE
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        return TypingIconColor.BLACK if brightness > 125 else TypingIconColor.WHITE

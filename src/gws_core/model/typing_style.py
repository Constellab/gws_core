# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from enum import Enum
from typing import Optional

from gws_core.core.model.model_dto import BaseModelDTO


class TypingIconType(Enum):
    MATERIAL_ICON = "MATERIAL_ICON"
    COMMUNITY_ICON = "COMMUNITY_ICON"
    COMMUNITY_IMAGE = "COMMUNITY_IMAGE"


class TypingIconColor(Enum):
    WHITE = "#FFFFFF"
    BLACK = "#000000"


class TypingStyle(BaseModelDTO):

    icon: str = None
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
    def material_icon(icon: str, background_color: str = None,
                      icon_color: Optional[TypingIconColor] = None) -> 'TypingStyle':
        return TypingStyle(icon=icon,
                           icon_type=TypingIconType.MATERIAL_ICON,
                           background_color=background_color,
                           icon_color=icon_color)

    @staticmethod
    def community_icon(icon: str, background_color: str = None,
                       icon_color: Optional[TypingIconColor] = None) -> 'TypingStyle':
        return TypingStyle(icon=icon,
                           icon_type=TypingIconType.COMMUNITY_ICON,
                           background_color=background_color,
                           icon_color=icon_color)

    @staticmethod
    def community_image(icon: str, background_color: str = None) -> 'TypingStyle':
        return TypingStyle(icon=icon,
                           icon_type=TypingIconType.COMMUNITY_IMAGE,
                           background_color=background_color,
                           icon_color=None)

    @staticmethod
    def default_resource() -> 'TypingStyle':
        return TypingStyle(icon="resource",
                           icon_type=TypingIconType.MATERIAL_ICON,
                           background_color="#af3e01",
                           icon_color=TypingIconColor.WHITE)

    @staticmethod
    def default_task() -> 'TypingStyle':
        return TypingStyle(icon="process",
                           icon_type=TypingIconType.MATERIAL_ICON,
                           background_color="#af3e01",
                           icon_color=TypingIconColor.WHITE)

    @staticmethod
    def default_protocol() -> 'TypingStyle':
        return TypingStyle(icon="protocol",
                           icon_type=TypingIconType.MATERIAL_ICON,
                           background_color="#af3e01",
                           icon_color=TypingIconColor.WHITE)

    @staticmethod
    def get_contrast_color(color: str) -> TypingIconColor:
        if color is None:
            return TypingIconColor.WHITE
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        return TypingIconColor.BLACK if brightness > 125 else TypingIconColor.WHITE

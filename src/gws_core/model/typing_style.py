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

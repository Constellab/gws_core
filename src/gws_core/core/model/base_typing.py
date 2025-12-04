from typing import final

from gws_core.brick.brick_helper import BrickHelper
from gws_core.core.db.version import Version
from gws_core.core.model.base import Base
from gws_core.model.typing_name import TypingNameObj
from gws_core.model.typing_style import TypingStyle


class BaseTyping(Base):
    # Provided at the Class level automatically by the Decorator
    # //!\\ Do not modify theses values
    __typing_name__: str = None
    __human_name__: str = None
    __short_description__: str = None
    __style__: TypingStyle = None

    @final
    @classmethod
    def get_typing_name(cls) -> str:
        """Get the typing name of the object
        Ex: 'RESOURCE.gws_core.Table'

        :return: typing name
        :rtype: str
        """
        return cls.__typing_name__

    @final
    @classmethod
    def get_human_name(cls) -> str:
        """Get the human name of the object

        :return: human name
        :rtype: str
        """
        return cls.__human_name__

    @final
    @classmethod
    def get_short_description(cls) -> str:
        """Get the short description of the object

        :return: short description
        :rtype: str
        """
        return cls.__short_description__

    @final
    @classmethod
    def get_style(cls) -> TypingStyle:
        """Get the style of the object

        :return: style
        :rtype: str
        """
        return cls.__style__

    @final
    @classmethod
    def get_typing_name_obj(cls) -> TypingNameObj:
        return TypingNameObj.from_typing_name(cls.get_typing_name())

    @final
    @classmethod
    def get_brick_name(cls) -> str:
        return cls.get_typing_name_obj().brick_name

    @final
    @classmethod
    def get_brick_version(cls) -> Version:
        return BrickHelper.get_brick_version(cls.get_brick_name())

    ############################################### SYSTEM METHODS ####################################################

    @final
    @classmethod
    def __set_typing_name__(cls, typing_name: str) -> None:
        """Set the typing name of the object
        This method is called by the system when the object is created,
        you should not call this method yourself

        :param typing_name: typing name
        :type typing_name: str
        """
        cls.__typing_name__ = typing_name

    @final
    @classmethod
    def __set_human_name__(cls, human_name: str) -> None:
        """Set the human name of the object
        This method is called by the system when the object is created,
        you should not call this method yourself

        :param human_name: human name
        :type human_name: str
        """
        cls.__human_name__ = human_name

    @final
    @classmethod
    def __set_short_description__(cls, short_description: str) -> None:
        """Set the short description of the object
        This method is called by the system when the object is created,
        you should not call this method yourself

        :param short_description: short description
        :type short_description: str
        """
        cls.__short_description__ = short_description

    @final
    @classmethod
    def __set_style__(cls, style: TypingStyle) -> None:
        """Set the style of the object
        This method is called by the system when the object is created,
        you should not call this method yourself

        :param style: style
        :type style: str
        """
        cls.__style__ = style

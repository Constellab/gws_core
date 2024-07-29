

from typing import final

from gws_core.core.model.base import Base


class BaseTyping(Base):

    # Provided at the Class level automatically by the Decorator
    # //!\\ Do not modify theses values
    __typing_name__: str = None
    __human_name__: str = None
    __short_description__: str = None

    @final
    @classmethod
    def get_typing_name(cls) -> str:
        """Get the typing name of the resource

        :return: typing name
        :rtype: str
        """
        return cls.__typing_name__

    @final
    @classmethod
    def get_human_name(cls) -> str:
        """Get the human name of the resource

        :return: human name
        :rtype: str
        """
        return cls.__human_name__

    @final
    @classmethod
    def get_short_description(cls) -> str:
        """Get the short description of the resource

        :return: short description
        :rtype: str
        """
        return cls.__short_description__

    ############################################### SYSTEM METHODS ####################################################

    @final
    @classmethod
    def __set_typing_name__(cls, typing_name: str) -> None:
        """Set the typing name of the resource
        This method is called by the system when the resource is created,
        you should not call this method yourself

        :param typing_name: typing name
        :type typing_name: str
        """
        cls.__typing_name__ = typing_name

    @final
    @classmethod
    def __set_human_name__(cls, human_name: str) -> None:
        """Set the human name of the resource
        This method is called by the system when the resource is created,
        you should not call this method yourself

        :param human_name: human name
        :type human_name: str
        """
        cls.__human_name__ = human_name

    @final
    @classmethod
    def __set_short_description__(cls, short_description: str) -> None:
        """Set the short description of the resource
        This method is called by the system when the resource is created,
        you should not call this method yourself

        :param short_description: short description
        :type short_description: str
        """
        cls.__short_description__ = short_description

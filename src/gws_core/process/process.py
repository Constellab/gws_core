# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from abc import abstractmethod

from gws_core.io.io_spec_helper import InputSpecs, OutputSpecs

from ..core.model.base import Base
from ..user.user_group import UserGroup


class Process(Base):

    # Provided at the Class level automatically by the Decorator
    # //!\\ Do not modify theses values
    _typing_name: str = None
    _human_name: str = None
    _short_description: str = None
    _allowed_user: UserGroup = UserGroup.USER

    @classmethod
    @abstractmethod
    def get_input_specs(cls) -> InputSpecs:
        """ Returns the input specs of the process """

    @classmethod
    @abstractmethod
    def get_output_specs(cls) -> OutputSpecs:
        """ Returns the input specs of the process """

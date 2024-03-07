# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from abc import abstractmethod
from typing import List, Type, final

from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.resource.resource import Resource

from ..core.model.base import Base
from ..user.user_group import UserGroup


class Process(Base):

    # Provided at the Class level automatically by the Decorator
    # //!\\ Do not modify theses values
    _typing_name: str = None
    _human_name: str = None
    _short_description: str = None
    # For specific tasks, the process is automatically run when added or reset
    # Set only on specific tasks when you know what you are doing
    __auto_run__: bool = False

    @classmethod
    @abstractmethod
    def get_input_specs(cls) -> InputSpecs:
        """ Returns the input specs of the process """

    @classmethod
    @abstractmethod
    def get_output_specs(cls) -> OutputSpecs:
        """ Returns the input specs of the process """

    @final
    @classmethod
    def get_compatible_input_name(cls, resource_types: List[Type[Resource]]) -> bool:
        """
        Returns the name of the first compatible input for the given resource types
        Returns None if no compatible input is found
        """
        for input_name, input in cls.get_input_specs().get_specs().items():
            if input.is_compatible_with_resource_types(resource_types):
                return input_name

        return None

    @final
    @classmethod
    def get_compatible_output_name(cls, resource_types: List[Type[Resource]]) -> bool:
        """
        Returns the name of the first compatible output for the given resource types
        Returns None if no compatible output is found
        """
        for output_name, output in cls.get_output_specs().get_specs().items():
            if output.is_compatible_with_resource_types(resource_types):
                return output_name

        return None

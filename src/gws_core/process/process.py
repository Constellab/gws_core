from abc import abstractmethod

from gws_core.core.model.base_typing import BaseTyping
from gws_core.io.io_specs import InputSpecs, OutputSpecs


class Process(BaseTyping):
    # Provided at the Class level automatically by the Decorator
    # //!\\ Do not modify theses values
    # For specific tasks, the process is automatically run when added or reset
    # Set only on specific tasks when you know what you are doing
    __auto_run__: bool = False

    # For specific tasks, it prevent the process for being added to a sub protocol
    # Set only on specific tasks when you know what you are doing
    __enable_in_sub_protocol__: bool = True

    # For specific tasks, defines the process as an agent
    __is_agent__: bool = False

    @classmethod
    @abstractmethod
    def get_input_specs(cls) -> InputSpecs:
        """Returns the input specs of the process"""

    @classmethod
    @abstractmethod
    def get_output_specs(cls) -> OutputSpecs:
        """Returns the input specs of the process"""

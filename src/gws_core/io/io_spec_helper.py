# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, Literal, Type

from ..brick.brick_service import BrickService
from .io_spec import InputSpec, OutputSpec, IOSpec, IOSpecDict

# Specs for a task Input
InputSpecs = Dict[str, InputSpec]

# Specs for a task Output
OutputSpecs = Dict[str, OutputSpec]

IOSpecs = Dict[str, IOSpec]


class IOSpecsHelper():
    """Class containing only class method to simplify IOSpecs management
    """

    @classmethod
    def io_specs_to_json(cls, io_specs: IOSpecs) -> Dict[str, IOSpecDict]:
        """to_json method for IOSpecs
        """

        json_:  Dict[str, IOSpecDict] = {}
        for key, spec in io_specs.items():
            json_[key] = spec.to_json()
        return json_

    @classmethod
    def check_input_specs(cls, input_specs: InputSpecs, task_type: Type) -> None:
        """Method to verify that input specs are valid
        """
        cls._check_io_spec_param(input_specs, 'input', InputSpec, task_type)

    @classmethod
    def check_output_specs(cls, output_specs: OutputSpecs, task_type: Type) -> None:
        """Method to verify that output specs are valid
        """
        cls._check_io_spec_param(output_specs, 'output', OutputSpec, task_type)

    @classmethod
    def _check_io_spec_param(cls, io_specs: IOSpecs,
                             param_type: Literal['input', 'output'], type_io: Type[IOSpec], task_type: Type) -> None:
        if not io_specs:
            return

        if not isinstance(io_specs, dict):
            raise Exception("The specs must be a dictionary")

        for key, item in io_specs.items():

            if not isinstance(item, IOSpec):
                # TODO for now this is just a warninig, to remove
                item = type_io(item)
                io_specs[key] = item
                BrickService.log_brick_warning(
                    task_type,
                    f"The {param_type} specs '{key}' of task '{task_type.__name__}' is not a TypeIO, please use InputSpec or OutputSpec")

            item.check_resource_types()

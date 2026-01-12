from typing import Literal, cast

from ..brick.brick_service import BrickService
from .io_spec import IOSpec
from .io_specs import InputSpecs, IOSpecs, OutputSpecs


class IOSpecsHelper:
    """Class containing only class method to simplify IOSpecs management"""

    @classmethod
    def check_input_specs(cls, input_specs: InputSpecs, task_type: type) -> InputSpecs:
        """Method to verify that input specs are valid"""
        return cast(InputSpecs, cls._check_io_spec_param(input_specs, "input", task_type))

    @classmethod
    def check_output_specs(cls, output_specs: OutputSpecs, task_type: type) -> OutputSpecs:
        """Method to verify that output specs are valid"""
        return cast(OutputSpecs, cls._check_io_spec_param(output_specs, "output", task_type))

    @classmethod
    def _check_io_spec_param(
        cls, io_specs: IOSpecs, param_type: Literal["input", "output"], task_type: type
    ) -> IOSpecs:
        if not io_specs:
            io_specs = InputSpecs() if param_type == "input" else OutputSpecs()

        # TODO for now this is just a warning
        if not isinstance(io_specs, IOSpecs):
            BrickService.log_brick_warning(
                task_type,
                f"The specs of task {task_type.__name__} must be an InputSpecs or OutputSpecs",
            )
            io_specs = InputSpecs(io_specs) if param_type == "input" else OutputSpecs(io_specs)

        if not isinstance(io_specs.get_specs(), dict):
            raise Exception("The specs must be a dictionary")

        for key, item in io_specs.get_specs().items():
            if not isinstance(item, IOSpec):
                error = f"The {param_type} specs '{key}' of task '{task_type.__name__}' is not a TypeIO, please use InputSpec or OutputSpec"
                BrickService.log_brick_error(task_type, error)
                raise Exception(error)

            item.check_resource_types()

        return io_specs

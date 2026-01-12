from typing import Literal, cast

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.utils.logger import Logger
from gws_core.io.io_exception import InvalidInputsException, MissingInputResourcesException
from gws_core.io.io_spec import InputSpec, IOSpec, IOSpecDTO, OutputSpec
from gws_core.resource.resource import Resource
from gws_core.resource.resource_factory import ResourceFactory
from gws_core.task.task_io import TaskInputs, TaskOutputs

IOSpecsType = Literal["normal", "dynamic"]


class IOSpecsDTO(BaseModelDTO):
    """IOSpecsDTO type"""

    specs: dict[str, IOSpecDTO]
    type: IOSpecsType
    additional_info: dict

    def to_markdown(self) -> str:
        markdown = ""
        for spec in self.specs.values():
            markdown += spec.to_markdown() + "\n"
        return markdown


class OutputsCheckResult(BaseModelDTO):
    """OutputCheckResult type"""

    error: str | None
    outputs: TaskOutputs | None
    auto_convert_messages: list[str]

    class Config:
        arbitrary_types_allowed = True


class OutputCheckResult(BaseModelDTO):
    """OutputCheckResult type"""

    error: str | None
    resource: Resource | None
    auto_convert_message: str | None

    class Config:
        arbitrary_types_allowed = True


class IOSpecs:
    _specs: dict[str, IOSpec] = {}

    def __init__(self, specs: dict[str, IOSpec] | None = None) -> None:
        if specs is None:
            specs = {}
        if not isinstance(specs, dict):
            raise Exception("The specs must be a dictionary")
        self._specs = specs

    def get_specs(self) -> dict[str, IOSpec]:
        return self._specs

    def get_spec(self, name: str) -> IOSpec:
        return self._specs[name]

    def has_spec(self, name: str) -> bool:
        return name in self._specs

    def get_type(self) -> IOSpecsType:
        return "normal"

    def get_additional_info(self) -> dict:
        return {}

    def set_additional_info(self, additional_info: dict) -> None:
        pass

    def get_first_spec(self) -> IOSpec | None:
        if len(self._specs) == 0:
            return None
        return list(self._specs.values())[0]

    def to_dto(self) -> IOSpecsDTO:
        spec_dto = IOSpecsDTO(
            specs={}, type=self.get_type(), additional_info=self.get_additional_info()
        )

        for key, spec in self.get_specs().items():
            spec_dto.specs[key] = spec.to_dto()

        return spec_dto


class InputSpecs(IOSpecs):
    _specs: dict[str, InputSpec] = {}

    def __init__(self, input_specs: dict[str, InputSpec] | None = None) -> None:
        super().__init__(cast(dict[str, IOSpec], input_specs))

    def check_and_build_inputs(self, inputs: dict[str, Resource]) -> TaskInputs:
        """Check and convert input to TaskInputs
        :rtype: TaskInputs
        """
        missing_resource: list[str] = []
        invalid_input_text: str = ""

        input_dict: dict[str, Resource | None] = {}

        for key, spec in self._specs.items():
            # If the resource is None
            if key not in inputs or inputs[key] is None:
                # If the resource is empty and the spec not optional, add an error
                if not spec.optional:
                    missing_resource.append(key)
                else:
                    input_dict[key] = None
                continue

            resource: Resource = inputs[key]
            if not spec.is_compatible_with_resource_type(type(resource)):
                invalid_input_text = (
                    invalid_input_text
                    + f"The input '{spec.human_name}' expected a '{spec.get_resources_human_names()}' but the provided resource is a '{resource.get_human_name()}'. Please provide a valid resource."
                )

            # validate the resource through the spec
            spec.validate_resource(resource)

            input_dict[key] = resource

        if len(missing_resource) > 0:
            raise MissingInputResourcesException(port_names=missing_resource)

        if invalid_input_text and len(invalid_input_text) > 0:
            raise InvalidInputsException(invalid_input_text)

        return TaskInputs(self._transform_input_resources(input_dict))

    def _transform_input_resources(
        self, resources: dict[str, Resource | None]
    ) -> dict[str, Resource | None]:
        """
        Returns the resources of all the ports to be used for the input of a task.
        """

        return resources


class OutputSpecs(IOSpecs):
    _specs: dict[str, OutputSpec] = {}

    def __init__(self, output_specs: dict[str, OutputSpec] | None = None) -> None:
        super().__init__(cast(dict[str, IOSpec], output_specs))

    def check_and_build_outputs(self, task_outputs: TaskOutputs) -> OutputsCheckResult:
        """Method that check if the task outputs

        :param task_outputs: outputs to check
        :type task_outputs: TaskOutputs
        :raises InvalidOutputException: raised if the output are invalid
        """

        if task_outputs is None:
            task_outputs = {}

        if not isinstance(task_outputs, dict):
            raise Exception("The task output is not a dictionary")

        task_outputs = self._transform_output_resources(task_outputs)

        error_text: str = ""
        auto_convert_messages: list[str] = []

        verified_outputs: TaskOutputs = {}

        for key, spec in self._specs.items():
            # handle the case where the output is None
            if key not in task_outputs or task_outputs[key] is None:
                if not spec.optional:
                    text = "was not provided" if key not in task_outputs else "is None"
                    error_text = (
                        error_text + f"The output '{self._get_spec_key_pretty_name(key)}' {text}."
                    )
                continue

            # If the resource for the output port was provided
            if key in task_outputs:
                resource: Resource = task_outputs[key]

                check_result = self._check_output(
                    resource, spec, self._get_spec_key_pretty_name(key)
                )

                # add the auto convert message
                if check_result.auto_convert_message is not None:
                    auto_convert_messages.append(check_result.auto_convert_message)

                # if there is an error, add it to the error text
                if check_result.error is not None and len(check_result.error) > 0:
                    error_text = error_text + check_result.error
                    continue

                # save the resource event if there is an error
                if isinstance(check_result.resource, Resource):
                    verified_outputs[key] = check_result.resource

        return OutputsCheckResult(
            error=error_text, outputs=verified_outputs, auto_convert_messages=auto_convert_messages
        )

    def _check_output(
        self, output_resource: Resource, spec: OutputSpec, pretty_key_name: str
    ) -> OutputCheckResult:
        """Method to check a output resource, return str if there is an error with the resource"""

        auto_convert_message: str | None = None
        # if the resource is not a Resource, try to convert it
        if not isinstance(output_resource, Resource):
            converted_resource = ResourceFactory.create_from_object(output_resource)
            if converted_resource is None:
                return OutputCheckResult(
                    error=f"The output '{pretty_key_name}' of type '{type(output_resource).__name__}' is not a resource and could not be converted dynamically. It must extend the Resource class",
                    resource=None,
                )

            auto_convert_message = f"The output '{pretty_key_name}' of type '{type(output_resource).__name__}' was automatically converted to '{type(converted_resource).get_human_name()}'."
            output_resource = converted_resource

        # Check resource is compatible with specs
        if not spec.is_compatible_with_resource_type(type(output_resource)):
            return OutputCheckResult(
                error=f"The output '{pretty_key_name}' of type '{type(output_resource).__name__}' is not a compatble with the corresponding output spec.",
                resource=None,
                auto_convert_message=auto_convert_message,
            )

        # Check that the resource is well formed
        try:
            error = output_resource.check_resource()

            if error is not None and len(error) > 0:
                return OutputCheckResult(
                    error=error, resource=None, auto_convert_message=auto_convert_message
                )

        except Exception as err:
            Logger.log_exception_stack_trace(err)
            return OutputCheckResult(
                error=f"Error during the key of the output resource '{pretty_key_name}'. Error : {str(err)}",
                resource=None,
                auto_convert_message=auto_convert_message,
            )

        return OutputCheckResult(
            resource=output_resource, error=None, auto_convert_message=auto_convert_message
        )

    def _transform_output_resources(self, task_outputs: TaskOutputs) -> TaskOutputs:
        """Method to convert the task output to be saved in the outputs.
        If the output is not dynamic, it returns the task_outputs as it is.
        """
        return task_outputs

    def _get_spec_key_pretty_name(self, key: str) -> str:
        """Get the pretty name of the spec key"""
        return key

# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from typing import Dict, List, Literal, TypedDict

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.utils.logger import Logger
from gws_core.io.io_exception import (InvalidInputsException,
                                      MissingInputResourcesException)
from gws_core.io.io_spec import (InputSpec, IOSpec, IOSpecDict, IOSpecDTO,
                                 OutputSpec)
from gws_core.resource.resource import Resource
from gws_core.resource.resource_factory import ResourceFactory
from gws_core.task.task_io import TaskInputs, TaskOutputs

IOSpecsType = Literal['normal', 'dynamic']

# TODO TO REMOVE


class IOSpecsDict(TypedDict):
    """IOSpecsDict type
    """
    specs: Dict[str, IOSpecDict]
    type: IOSpecsType
    additional_info: dict


class IOSpecsDTO(BaseModelDTO):
    """IOSpecsDTO type
    """
    specs: Dict[str, IOSpecDTO]
    type: IOSpecsType
    additional_info: dict


class OutputsCheckResult(TypedDict):
    """OutputCheckResult type
    """
    error: str
    outputs: TaskOutputs


class OutputCheckResult(TypedDict):
    """OutputCheckResult type
    """
    error: str
    resource: Resource


class IOSpecs():

    _specs: Dict[str, IOSpec] = {}

    def __init__(self, specs: Dict[str, IOSpec] = None) -> None:
        if specs is None:
            specs = {}
        if not isinstance(specs, dict):
            raise Exception("The specs must be a dictionary")
        self._specs = specs

    def get_specs(self) -> Dict[str, IOSpec]:
        return self._specs

    def get_spec(self, name: str) -> IOSpec:
        return self._specs[name]

    def has_spec(self, name: str) -> bool:
        return name in self._specs

    def get_type(self) -> IOSpecsType:
        return 'normal'

    def get_additional_info(self) -> dict:
        return {}

    def set_additional_info(self, additional_info: dict) -> None:
        pass

    def to_json(self) -> IOSpecsDict:
        """to_json method for IOSpecs
        """

        json_:  IOSpecsDict = {
            "specs": {},
            "type": self.get_type(),
            "additional_info": self.get_additional_info()
        }
        for key, spec in self.get_specs().items():
            json_["specs"][key] = spec.to_json()
        return json_

    def to_dto(self) -> IOSpecsDTO:
        spec_dto = IOSpecsDTO(
            specs={},
            type=self.get_type(),
            additional_info=self.get_additional_info()
        )

        for key, spec in self.get_specs().items():
            spec_dto.specs[key] = spec.to_dto()

        return spec_dto


class InputSpecs(IOSpecs):

    _specs: Dict[str, InputSpec] = {}

    def __init__(self, input_specs: Dict[str, InputSpec] = None) -> None:
        super().__init__(input_specs)

    def check_and_build_inputs(self, inputs: Dict[str, Resource]) -> TaskInputs:
        """Check and convert input to TaskInputs
        :rtype: TaskInputs
        """
        missing_resource: List[str] = []
        invalid_input_text: str = ''

        input_dict: Dict[str, Resource] = {}

        for key, spec in self._specs.items():
            # If the resource is None
            if key not in inputs or inputs[key] is None:
                # If the resource is empty and the spec not optional, add an error
                if not spec.is_optional:
                    missing_resource.append(key)
                else:
                    input_dict[key] = None
                continue

            resource: Resource = inputs[key]
            if not spec.is_compatible_with_resource_type(type(resource)):
                invalid_input_text = invalid_input_text + \
                    f"The input '{key}' of type '{resource._typing_name}' is not a compatible with the corresponding input spec."

            # validate the resource through the spec
            spec.validate_resource(resource)

            input_dict[key] = resource

        if len(missing_resource) > 0:
            raise MissingInputResourcesException(port_names=missing_resource)

        if invalid_input_text and len(invalid_input_text) > 0:
            raise InvalidInputsException(invalid_input_text)

        return TaskInputs(self._transform_input_resources(input_dict))

    def _transform_input_resources(self, resources: Dict[str, Resource]) -> Dict[str, Resource]:
        """
        Returns the resources of all the ports to be used for the input of a task.
        """

        return resources


class OutputSpecs(IOSpecs):

    _specs: Dict[str, OutputSpec] = {}

    def __init__(self, output_specs: Dict[str, OutputSpec] = None) -> None:
        super().__init__(output_specs)

    def check_and_build_outputs(self, task_outputs: TaskOutputs) -> OutputsCheckResult:
        """Method that check if the task outputs

        :param task_outputs: outputs to check
        :type task_outputs: TaskOutputs
        :raises InvalidOutputException: raised if the output are invalid
        """

        if task_outputs is None:
            task_outputs = {}

        if not isinstance(task_outputs, dict):
            raise Exception('The task output is not a dictionary')

        task_outputs = self._transform_output_resources(task_outputs)

        error_text: str = ''

        verified_outputs: TaskOutputs = {}

        for key, spec in self._specs.items():

            # handle the case where the output is None
            if key not in task_outputs or task_outputs[key] is None:
                if not spec.is_optional:
                    text = "was not provided" if key not in task_outputs else "is None"
                    error_text = error_text + \
                        f"The output '{self._get_spec_key_pretty_name(key)}' {text}."
                continue

            # If the resource for the output port was provided
            if key in task_outputs:
                resource: Resource = task_outputs[key]

                check_result = self._check_output(resource, spec, self._get_spec_key_pretty_name(key))
                if check_result["error"] is not None and len(check_result["error"]) > 0:
                    error_text = error_text + check_result["error"]
                    continue

                # save the resource event if there is an error
                if isinstance(check_result["resource"], Resource):
                    verified_outputs[key] = check_result["resource"]

        return {
            "error": error_text,
            "outputs": verified_outputs
        }

    def _check_output(self, output_resource: Resource, spec: OutputSpec, pretty_key_name: str) -> OutputCheckResult:
        """Method to check a output resource, return str if there is an error with the resource
        """

        # if the resource is not a Resource, try to convert it
        if not isinstance(output_resource, Resource):
            resource_type = type(output_resource)
            output_resource = ResourceFactory.create_from_object(output_resource)
            if output_resource is None:
                return {
                    "error": f"The output '{pretty_key_name}' of type '{resource_type.__name__}' is not a resource and could not be converted dynamically. It must extend the Resource class",
                    "resource": None
                }

        # Check resource is compatible with specs
        if not spec.is_compatible_with_resource_type(type(output_resource)):
            return {
                "error": f"The output '{pretty_key_name}' of type '{type(output_resource).__name__}' is not a compatble with the corresponding output spec.",
                "resource": None
            }

        # Check that the resource is well formed
        try:
            error = output_resource.check_resource()

            if error is not None and len(error) > 0:
                return {"error": error, "resource": None}

        except Exception as err:
            Logger.log_exception_stack_trace(err)
            return {"error": f"Error during the key of the output resource '{pretty_key_name}'. Error : {str(err)}", "resource": None}

        return {
            "resource": output_resource,
            "error": None
        }

    def _transform_output_resources(self, task_outputs: TaskOutputs) -> TaskOutputs:
        """ Method to convert the task output to be saved in the outputs.
        If the output is not dynamic, it returns the task_outputs as it is.
        """
        return task_outputs

    def _get_spec_key_pretty_name(self, key: str) -> str:
        """Get the pretty name of the spec key
        """
        return key

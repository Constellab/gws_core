# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, List, Optional

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.io.io_specs import IOSpecsType
from gws_core.resource.resource import Resource
from gws_core.resource.resource_set.resource_list import ResourceList
from gws_core.task.task_io import TaskOutputs

from .io_spec import InputSpec, IOSpecDTO, OutputSpec
from .io_specs import InputSpecs, OutputSpecs


class AdditionalInfo(BaseModelDTO):
    additionnal_port_spec: Optional[IOSpecDTO]


class DynamicInputs(InputSpecs):

    # name of the spec passed to the task
    SPEC_NAME = 'source'

    additionnal_port_spec: InputSpec = None

    def __init__(self, default_specs: Dict[str, InputSpec] = None,
                 additionnal_port_spec: InputSpec = None) -> None:
        """
        :param default_specs: default specs used when creating the inputs, defaults to None
        :type default_specs: Dict[str, InputSpec], optional
        :param additionnal_port_spec: force the type of newly created port, defaults to Resource
        :type additionnal_port_spec: Type[Resource], optional
        """
        self.additionnal_port_spec = additionnal_port_spec
        if default_specs is None:
            # set 1 input spec by default
            default_specs = {"source": self.get_default_spec()}
        super().__init__(default_specs)

    def get_type(self) -> IOSpecsType:
        return 'dynamic'

    def get_additional_info(self) -> dict:
        return AdditionalInfo(
            additionnal_port_spec=self.additionnal_port_spec.to_dto() if self.additionnal_port_spec else None
        ).to_json_dict()

    def set_additional_info(self, additional_info: dict) -> None:
        if not additional_info:
            return

        additional_info_dto = AdditionalInfo.from_json(additional_info)

        if additional_info_dto.additionnal_port_spec:
            self.additionnal_port_spec = InputSpec.from_dto(additional_info_dto.additionnal_port_spec)

    def _transform_input_resources(self, resources: Dict[str, Resource]) -> Dict[str, Resource]:
        """
        Returns the resources of all the ports to be used for the input of a task.

        as this is dynamic, we return only the resources of the 'source' port which is a ResourceList
        """

        resources_list: List[Resource] = list(resources.values())
        return {self.SPEC_NAME: ResourceList(resources_list)}

    def get_default_spec(self) -> InputSpec:
        if self.additionnal_port_spec:
            return self.additionnal_port_spec

        return InputSpec(Resource, is_optional=True)

    @classmethod
    def from_dto(cls, io_specs: Dict[str, InputSpec], additional_info: dict) -> 'DynamicInputs':
        dynamic_inputs = cls(io_specs)
        dynamic_inputs.set_additional_info(additional_info)
        return dynamic_inputs


class DynamicOutputs(OutputSpecs):

    # name of the spec passed to the task
    SPEC_NAME = 'target'

    additionnal_port_spec: OutputSpec = None

    def __init__(self, default_specs: Dict[str, OutputSpec] = None,
                 additionnal_port_spec: OutputSpec = None) -> None:
        """
        :param default_specs: default specs used when creating the outputs, defaults to None
        :type default_specs: Dict[str, OutputSpec], optional
        :param additionnal_port_spec: force the type of newly created port, defaults to Resource
        :type additionnal_port_spec: Type[Resource], optional
        """

        if default_specs is None:
            # set 1 output spec by default
            default_specs = {"target": self.get_default_spec()}
        super().__init__(default_specs)

        self.additionnal_port_spec = additionnal_port_spec

    def get_type(self) -> IOSpecsType:
        return 'dynamic'

    def get_additional_info(self) -> dict:
        return AdditionalInfo(
            additionnal_port_spec=self.additionnal_port_spec.to_dto() if self.additionnal_port_spec else None
        ).to_json_dict()

    def set_additional_info(self, additional_info: dict) -> None:
        if not additional_info:
            return

        additional_info_dto = AdditionalInfo.from_json(additional_info)

        if additional_info_dto.additionnal_port_spec:
            self.additionnal_port_spec = OutputSpec.from_dto(additional_info_dto.additionnal_port_spec)

    def _transform_output_resources(self, task_outputs: TaskOutputs) -> TaskOutputs:
        """ Method to convert the task output to be saved in the outputs.

        If task output is dynamic, it converts the ResourceList to a basic task output dict with the port
        name as key and the resource as value based on the index of the resource in the ResourceList
        """
        if self.SPEC_NAME not in task_outputs:
            raise Exception(f"Output {self.SPEC_NAME} not found in task outputs")

        target = task_outputs['target']

        # check if target is a iterable
        if not hasattr(target, '__iter__'):
            raise Exception(f"Output {self.SPEC_NAME} must be an iterable of resources, got {type(target)}")

        resource_list: List[Resource] = list(target)

        output_resources = {}

        port_keys = list(self._specs.keys())

        if len(resource_list) > len(port_keys):
            raise Exception(
                f"Too many resources in output {self.SPEC_NAME}, expected {len(port_keys)} got {len(resource_list)}")
        if resource_list:
            count = 0
            for resource in resource_list:
                output_resources[port_keys[count]] = resource
                count += 1

        return output_resources

    def _get_spec_key_pretty_name(self, key: str) -> str:
        """Get the pretty name of the spec key. As the key are UUID, we return the index of the spec key
        """
        # retrieve the index of the spec key
        index = list(self._specs.keys()).index(key)
        return f"n°{index + 1}"

    def get_default_spec(self) -> OutputSpec:
        if self.additionnal_port_spec:
            return self.additionnal_port_spec

        return OutputSpec(Resource, sub_class=True)

    @classmethod
    def from_dto(cls, io_specs: Dict[str, OutputSpec], additional_info: dict) -> 'DynamicOutputs':
        dynamic_outputs = cls(io_specs)
        dynamic_outputs.set_additional_info(additional_info)
        return dynamic_outputs

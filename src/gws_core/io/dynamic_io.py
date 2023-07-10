# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, List

from gws_core.resource.resource import Resource
from gws_core.resource.resource_set.resource_list import ResourceList
from gws_core.task.task_io import TaskOutputs

from .io_spec import InputSpec, OutputSpec
from .io_specs import InputSpecs, OutputSpecs


class DynamicInputs(InputSpecs):

    # name of the spec passed to the task
    SPEC_NAME = 'source'

    def __init__(self, default_specs: Dict[str, InputSpec] = None) -> None:
        if default_specs is None:
            # set 1 input spec by default
            default_specs = {"source": self.get_default_spec()}
        super().__init__(default_specs)

    def is_dynamic(self) -> bool:
        return True

    def _transform_input_resources(self, resources: Dict[str, Resource]) -> Dict[str, Resource]:
        """
        Returns the resources of all the ports to be used for the input of a task.

        as this is dynamic, we return only the resources of the 'source' port which is a ResourceList
        """

        resources: List[Resource] = list(resources.values())
        return {self.SPEC_NAME: ResourceList(resources)}

    @classmethod
    def get_default_spec(cls) -> InputSpec:
        return InputSpec(Resource, is_optional=True)


class DynamicOutputs(OutputSpecs):

    # name of the spec passed to the task
    SPEC_NAME = 'target'

    def __init__(self, default_specs: Dict[str, OutputSpec] = None) -> None:
        if default_specs is None:
            # set 1 output spec by default
            default_specs = {"target": self.get_default_spec()}
        super().__init__(default_specs)

    def is_dynamic(self) -> bool:
        return True

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

    @classmethod
    def get_default_spec(cls) -> OutputSpec:
        return OutputSpec(Resource, sub_class=True)

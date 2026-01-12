from collections.abc import Iterable
from typing import cast

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.io.io_specs import IOSpecsType
from gws_core.resource.resource import Resource
from gws_core.resource.resource_set.resource_list import ResourceList
from gws_core.task.task_io import TaskOutputs

from .io_spec import InputSpec, IOSpecDTO, OutputSpec
from .io_specs import InputSpecs, OutputSpecs


class AdditionalInfo(BaseModelDTO):
    """Data transfer object for storing additional information about dynamic IO specifications.

    This class is used to serialize and deserialize additional port specification information
    for dynamic inputs and outputs. It allows the system to persist and restore the configuration
    of dynamically created ports.

    Attributes:
        additionnal_port_spec: Optional specification for additional ports that can be dynamically
            created. This defines the type and constraints for newly added ports.
    """

    additionnal_port_spec: IOSpecDTO | None


class DynamicInputs(InputSpecs):
    """Dynamic input specification that allows tasks to have a variable number of input ports.

    This class enables tasks to accept a dynamic number of input resources that can be added
    or removed at runtime. All input resources are aggregated into a single ResourceList that
    is passed to the task under the name specified by SPEC_NAME ('source').

    Dynamic inputs are useful for tasks that need to process an arbitrary number of similar
    resources, such as merging multiple files or combining multiple datasets.

    Attributes:
        SPEC_NAME: The name of the input parameter passed to the task ('source'). This is the
            key under which the aggregated ResourceList will be available.
        additionnal_port_spec: Optional specification that defines the type and constraints
            for dynamically created input ports. If None, defaults to accepting any Resource type.

    Example:
        ```python
        # Define dynamic inputs that accept Table resources
        inputs = DynamicInputs(
            additionnal_port_spec=InputSpec(Table, human_name="Input table")
        )

        # In the task's run method:
        def run(self, params: ConfigParams, inputs: InputsDTO) -> OutputsDTO:
            # Access all inputs as a ResourceList
            sources: ResourceList = inputs['source']
            # Process each table
            for table in sources:
                # Process table...
        ```
    """

    # name of the spec passed to the task
    SPEC_NAME = "source"

    additionnal_port_spec: InputSpec | None = None

    def __init__(
        self,
        default_specs: dict[str, InputSpec] | None = None,
        additionnal_port_spec: InputSpec | None = None,
    ) -> None:
        """
        :param default_specs: default specs used when creating the inputs, defaults to None
        :type default_specs: Dict[str, InputSpec], optional
        :param additionnal_port_spec: force the type of newly created port, defaults to Resource
        :type additionnal_port_spec: InputSpec, optional
        """
        self.additionnal_port_spec = additionnal_port_spec
        if default_specs is None:
            # set 1 input spec by default
            default_specs = {"source": self.get_default_spec()}
        super().__init__(default_specs)

    def get_type(self) -> IOSpecsType:
        return "dynamic"

    def get_additional_info(self) -> dict:
        return AdditionalInfo(
            additionnal_port_spec=self.additionnal_port_spec.to_dto()
            if self.additionnal_port_spec
            else None
        ).to_json_dict()

    def set_additional_info(self, additional_info: dict | None) -> None:
        if not additional_info:
            return

        additional_info_dto = AdditionalInfo.from_json(additional_info)

        if additional_info_dto.additionnal_port_spec:
            self.additionnal_port_spec = InputSpec.from_dto(
                additional_info_dto.additionnal_port_spec
            )

    def _transform_input_resources(self, resources: dict[str, Resource]) -> dict[str, Resource]:
        """
        Returns the resources of all the ports to be used for the input of a task.

        as this is dynamic, we return only the resources of the 'source' port which is a ResourceList
        """

        resources_list: list[Resource] = list(resources.values())
        return {self.SPEC_NAME: ResourceList(resources_list)}

    def get_default_spec(self) -> InputSpec:
        if self.additionnal_port_spec:
            return self.additionnal_port_spec

        return InputSpec(Resource, optional=True)

    @classmethod
    def from_dto(
        cls, io_specs: dict[str, InputSpec], additional_info: dict | None
    ) -> "DynamicInputs":
        dynamic_inputs = cls(io_specs)
        dynamic_inputs.set_additional_info(additional_info)
        return dynamic_inputs


class DynamicOutputs(OutputSpecs):
    """Dynamic output specification that allows tasks to have a variable number of output ports.

    This class enables tasks to produce a variable number of output resources that can be defined
    at runtime. The task should return an iterable of resources under the name specified by
    SPEC_NAME ('target'), which will be automatically distributed to the individual output ports
    based on their order.

    Dynamic outputs are useful for tasks that produce an unpredictable number of results, such as
    splitting a file into multiple parts or generating multiple datasets from a single analysis.

    Attributes:
        SPEC_NAME: The name of the output parameter the task should return ('target'). The task
            must return an iterable of resources under this key.
        additionnal_port_spec: Optional specification that defines the type and constraints
            for dynamically created output ports. If None, defaults to accepting any Resource subclass.

    Example:
        ```python
        # Define dynamic outputs that produce Table resources
        outputs = DynamicOutputs(
            additionnal_port_spec=OutputSpec(Table, human_name="Output table")
        )

        # In the task's run method:
        def run(self, params: ConfigParams, inputs: InputsDTO) -> OutputsDTO:
            # Create multiple output tables
            tables = [table1, table2, table3]
            # Return as an iterable under 'target'
            return {'target': tables}
        ```

    Notes:
        - The number of resources in the returned iterable must not exceed the number of
          configured output ports.
        - Resources are assigned to ports based on their order in the iterable and the order
          of the port keys.
        - If fewer resources are returned than there are ports, remaining ports will be empty.
    """

    # name of the spec passed to the task
    SPEC_NAME = "target"

    additionnal_port_spec: OutputSpec | None = None

    def __init__(
        self,
        default_specs: dict[str, OutputSpec] | None = None,
        additionnal_port_spec: OutputSpec | None = None,
    ) -> None:
        """
        :param default_specs: default specs used when creating the outputs, defaults to None
        :type default_specs: Dict[str, OutputSpec], optional
        :param additionnal_port_spec: force the type of newly created port, defaults to Resource
        :type additionnal_port_spec: Type[Resource], optional
        """
        self.additionnal_port_spec = additionnal_port_spec
        if default_specs is None:
            # set 1 output spec by default
            default_specs = {"target": self.get_default_spec()}
        super().__init__(default_specs)

        self.additionnal_port_spec = additionnal_port_spec

    def get_type(self) -> IOSpecsType:
        return "dynamic"

    def get_additional_info(self) -> dict:
        return AdditionalInfo(
            additionnal_port_spec=self.additionnal_port_spec.to_dto()
            if self.additionnal_port_spec
            else None
        ).to_json_dict()

    def set_additional_info(self, additional_info: dict | None) -> None:
        if not additional_info:
            return

        additional_info_dto = AdditionalInfo.from_json(additional_info)

        if additional_info_dto.additionnal_port_spec:
            self.additionnal_port_spec = OutputSpec.from_dto(
                additional_info_dto.additionnal_port_spec
            )

    def _transform_output_resources(self, task_outputs: TaskOutputs) -> TaskOutputs:
        """Method to convert the task output to be saved in the outputs.

        If task output is dynamic, it converts the ResourceList to a basic task output dict with the port
        name as key and the resource as value based on the index of the resource in the ResourceList
        """
        if self.SPEC_NAME not in task_outputs:
            raise Exception(f"Output {self.SPEC_NAME} not found in task outputs")

        target = cast(Iterable[Resource], task_outputs["target"])

        # check if target is a iterable
        if not hasattr(target, "__iter__"):
            raise Exception(
                f"Output {self.SPEC_NAME} must be an iterable of resources, got {type(target)}"
            )

        resource_list: list[Resource] = list(target)

        output_resources = {}

        port_keys = list(self._specs.keys())

        if len(resource_list) > len(port_keys):
            raise Exception(
                f"Too many resources in output {self.SPEC_NAME}, expected {len(port_keys)} got {len(resource_list)}"
            )
        if resource_list:
            for count, resource in enumerate(resource_list):
                output_resources[port_keys[count]] = resource

        return output_resources

    def _get_spec_key_pretty_name(self, key: str) -> str:
        """Get the pretty name of the spec key. As the key are UUID, we return the index of the spec key"""
        # retrieve the index of the spec key
        index = list(self._specs.keys()).index(key)
        return f"n°{index + 1}"

    def get_default_spec(self) -> OutputSpec:
        if self.additionnal_port_spec:
            return self.additionnal_port_spec

        return OutputSpec(Resource, sub_class=True)

    @classmethod
    def from_dto(
        cls, io_specs: dict[str, OutputSpec], additional_info: dict | None
    ) -> "DynamicOutputs":
        dynamic_outputs = cls(io_specs)
        dynamic_outputs.set_additional_info(additional_info)
        return dynamic_outputs

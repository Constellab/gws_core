

from typing import List, Type

from gws_core.task.plug.input_task import InputTask as InputTask
from gws_core.task.plug.output_task import OutputTask as OutputTask
from gws_core.task.transformer.transformer import Transformer

from ...core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ...model.typing_manager import TypingManager
from ...process.process_proxy import ProcessProxy
from ...protocol.protocol_proxy import ProtocolProxy
from ...resource.resource import Resource
from ...resource.resource_model import ResourceModel
from ...scenario.scenario_proxy import ScenarioProxy
from ..converter.converter import Converter
from ..task import Task
from .transformer_type import TransformerDict


class TransformerService():

    @classmethod
    def create_and_run_transformer_scenario(cls, transformers: List[TransformerDict],
                                            resource_model_id: str) -> ResourceModel:

        if not transformers or len(transformers) == 0:
            raise BadRequestException('At least 1 transformer mustbe provided')

        # Get and check the resource id
        resource_model: ResourceModel = ResourceModel.get_by_id_and_check(
            resource_model_id)
        resource_type: Type[Resource] = resource_model.get_and_check_resource_type()

        # Create a scenario containing 1 source, X transformers task , 1 output task
        scenario: ScenarioProxy = ScenarioProxy(
            None, title=f"{resource_type.get_human_name()} transformation")
        protocol: ProtocolProxy = scenario.get_protocol()

        # create the source and save last process to create connectors later
        last_process: ProcessProxy = protocol.add_process(
            InputTask, 'source', {InputTask.config_name: resource_model_id})

        index: int = 1

        # create all transformer process with connectors
        for transformer in transformers:
            transformer_type: Type[Task] = TypingManager.get_and_check_type_from_name(
                transformer["typing_name"])

            new_process: ProcessProxy = protocol.add_process(
                transformer_type, f"transformer_{index}", transformer["config_values"])

            protocol.add_connector_by_names(last_process.instance_name, last_process.get_first_outport().port_name,
                                            new_process.instance_name, Transformer.input_name)

            # refresh data
            last_process = new_process
            index += 1

        # add output task
        protocol.add_output('output', last_process >> Transformer.output_name)

        #  run the scenario
        try:
            scenario.run()
        except Exception as exception:
            # delete scenario if there was an error
            scenario.delete()
            raise exception

        # return the resource model of the output process
        return scenario.get_model().protocol_model.get_process('output').inputs.get_resource_model(OutputTask.input_name)

    @classmethod
    def call_transformers(cls, resource: Resource,
                          transformers: List[TransformerDict]) -> Resource:

        # call all transformers in a raw
        for transformer in transformers:
            resource = cls.call_transformer(resource, transformer)

        return resource

    @classmethod
    def call_transformer(cls, resource: Resource,
                         transformer: TransformerDict) -> Resource:
        # retrieve transformer type
        transformer_task: Type[Converter] = TypingManager.get_and_check_type_from_name(
            transformer['typing_name'])

        return transformer_task.call(resource, transformer['config_values'])

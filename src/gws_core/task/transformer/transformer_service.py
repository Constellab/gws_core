# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Any, Coroutine, List, Type

from ...core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ...experiment.experiment import ExperimentType
from ...experiment.experiment_interface import IExperiment
from ...model.typing_manager import TypingManager
from ...process.process_interface import IProcess
from ...protocol.protocol_interface import IProtocol
from ...resource.resource import Resource
from ...resource.resource_model import ResourceModel
from ..converter.converter import ConverterRunner
from ..plug import Source
from ..task import Task
from .transformer_type import TransformerDict


class TransformerService():

    @classmethod
    async def create_and_run_transformer_experiment(cls, transformers: List[TransformerDict], resource_model_id: str) -> Coroutine[Any, Any, ResourceModel]:

        if not transformers or len(transformers) == 0:
            raise BadRequestException('At least 1 transformer mustbe provided')

        # Get and check the resource id
        resource_model: ResourceModel = ResourceModel.get_by_id_and_check(resource_model_id)
        resource_type: Type[Resource] = resource_model.get_resource_type()

        # Create an experiment containing 1 source, X transformers task , 1 sink
        experiment: IExperiment = IExperiment(
            None, title=f"{resource_type._human_name} transformation", type_=ExperimentType.TRANSFORMER)
        protocol: IProtocol = experiment.get_protocol()

        # create the source and save last process to create connectors later
        last_process: IProcess = protocol.add_process(Source, 'source', {'resource_id': resource_model_id})

        index: int = 1

        # create all transformer process with connectors
        for transformer in transformers:
            transformer_type: Type[Task] = TypingManager.get_type_from_name(transformer["typing_name"])

            new_process: IProcess = protocol.add_process(
                transformer_type, f"transformer_{index}", transformer["config_values"])

            protocol.add_connector(last_process.get_first_outport(), new_process << 'source')

            # refresh data
            last_process = new_process
            index += 1

        # add sink and sink connector
        protocol.add_sink('sink', last_process >> 'target')

        #  run the experiment
        try:
            await experiment.run()
        except Exception as exception:
            # delete experiment if there was an error
            experiment.delete()
            raise exception

        # return the resource model of the sink process
        return experiment.get_experiment_model().protocol_model.get_process('sink').inputs.get_resource_model('resource')

    @classmethod
    async def call_transformers(cls, resource: Resource,
                                transformers: List[TransformerDict]) -> Resource:

        # call all transformers in a raw
        for transformer in transformers:
            resource = await cls.call_transformer(resource, transformer)

        return resource

    @classmethod
    async def call_transformer(cls, resource: Resource,
                               transformer: TransformerDict) -> Resource:
        # retrieve transformer type
        transformer_task: Type[Task] = TypingManager.get_type_from_name(transformer['typing_name'])

        converter_runner: ConverterRunner = ConverterRunner(transformer_task, params=transformer['config_values'],
                                                            input=resource)

        # run task, clear after task and get resource
        resource: Resource = await converter_runner.run()
        await converter_runner.run_after_task()
        return resource

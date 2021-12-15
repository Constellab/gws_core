

from typing import Any, Coroutine, Type

from ...config.config_types import ConfigParamsDict, ConfigSpecsHelper
from ...core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ...core.utils.utils import Utils
from ...experiment.experiment import ExperimentType
from ...experiment.experiment_interface import IExperiment
from ...impl.file.file import File
from ...model.typing_manager import TypingManager
from ...process.process_interface import IProcess
from ...protocol.protocol_interface import IProtocol
from ...resource.resource_model import ResourceModel
from ...task.converter.importer import ResourceImporter
from ...task.plug import Sink, Source


class ConverterService:

    ################################################ IMPRTER ################################################

    @classmethod
    def get_import_specs(cls, resource_typing_name: str) -> dict:
        resource_type: Type[File] = TypingManager.get_type_from_name(resource_typing_name)

        importer_type: Type[ResourceImporter] = cls._get_and_check_resource_type_importer(resource_type)

        return ConfigSpecsHelper.config_specs_to_json(importer_type.config_specs)

    @classmethod
    async def call_importer(cls, resource_model_id: str, config: ConfigParamsDict) -> Coroutine[Any, Any, ResourceModel]:
        # Get and check the resource id
        resource_model: ResourceModel = ResourceModel.get_by_id_and_check(resource_model_id)
        resource_type: Type[File] = resource_model.get_resource_type()

        importer_type: Type[ResourceImporter] = cls._get_and_check_resource_type_importer(resource_type)

        # Create an experiment containing 1 source, 1 importer , 1 sink
        experiment: IExperiment = IExperiment(
            None, title=f"{resource_type._human_name} importer", type_=ExperimentType.TRANSFORMER)
        protocol: IProtocol = experiment.get_protocol()

        # create the source
        source: IProcess = protocol.add_process(Source, 'source', {'resource_id': resource_model_id})

        # Add the importer and the connector
        importer: IProcess = protocol.add_process(importer_type, 'importer', config)
        protocol.add_connector(source >> 'resource', importer << 'file')

        # add sink and sink connector
        sink = protocol.add_process(Sink, 'sink')
        protocol.add_connector(importer >> 'resource', sink << 'resource')

        # add the experiment to queue to run it
        await experiment.run()

        # return the resource model of the sink process
        return experiment.get_experiment_model().protocol_model.get_process('sink').inputs.get_resource_model('resource')

    @classmethod
    def _get_and_check_resource_type_importer(cls, resource_type: Type[File]) -> Type[ResourceImporter]:
        if not Utils.issubclass(resource_type, File):
            raise BadRequestException("Can't import this resource type")

        if resource_type._resource_importer is None:
            raise BadRequestException(
                "The resource must be an importable resource (using the importable_resource_decorator)")

    ################################################ EXPORTER ################################################

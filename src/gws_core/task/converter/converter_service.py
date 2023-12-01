# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import List, Type

from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.file.file_tasks import FsNodeExtractor
from gws_core.resource.resource import Resource
from gws_core.task.converter.exporter import ResourceExporter
from gws_core.task.plug import Sink

from ...config.config_types import ConfigParamsDict
from ...core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ...experiment.experiment_enums import ExperimentType
from ...experiment.experiment_interface import IExperiment
from ...impl.file.file import File
from ...model.typing_manager import TypingManager
from ...process.process_interface import IProcess
from ...protocol.protocol_interface import IProtocol
from ...resource.resource_model import ResourceModel
from ...task.converter.importer import ResourceImporter
from ...task.task_typing import TaskTyping


class ConverterService:

    ################################################ IMPORTER ################################################

    @classmethod
    def call_importer(
            cls, resource_model_id: str, importer_typing_name: str, config: ConfigParamsDict) -> ResourceModel:
        # Get and check the resource id
        resource_model: ResourceModel = ResourceModel.get_by_id_and_check(resource_model_id)
        resource_type: Type[File] = resource_model.get_resource_type()

        importer_type: Type[ResourceImporter] = TypingManager.get_type_from_name(importer_typing_name)

        # Create an experiment containing 1 source, 1 importer , 1 sink
        experiment: IExperiment = IExperiment(
            None, title=f"{resource_type._human_name} importer", type_=ExperimentType.IMPORTER)
        protocol: IProtocol = experiment.get_protocol()

        # Add the importer and the connector
        importer: IProcess = protocol.add_process(importer_type, 'importer', config)

        # Add source and connect it
        protocol.add_source('source', resource_model_id, importer << ResourceImporter.input_name)

        # Add sink and connect it
        sink = protocol.add_sink('sink', importer >> ResourceImporter.output_name)

        # run the experiment
        experiment.run(auto_delete_if_error=True)

        # return the resource model of the sink process
        sink.refresh()
        return sink.get_input_resource_model(Sink.input_name)

    ################################################ EXPORTER ################################################

    @classmethod
    def get_resource_exporter_from_name(cls, resource_typing_name: str) -> TaskTyping:
        """return the Task exporter typing for the resource type.
        The one that is closest to class in herarchy
        """
        resource_type: Type[File] = TypingManager.get_type_from_name(resource_typing_name)

        return cls.get_resource_exporter(resource_type)

    @classmethod
    def get_resource_exporter(cls, resource_type: Type[Resource]) -> TaskTyping:
        """return the Task exporter typing for the resource type.
        The one that is closest to class in herarchy
        """
        if not resource_type._is_exportable:
            raise BadRequestException(
                "The resource must be an exportable resource. This means that an exporter task must exist on for this resource")

        task_typings: List[TaskTyping] = TaskTyping.get_by_related_resource(resource_type, "EXPORTER")

        if len(task_typings) == 0:
            raise BadRequestException(f"Can't find the exporters for the resource type {resource_type._human_name}")

        # sort the list to have the most specific exporter first and generic last
        task_typings.sort(key=lambda x: len(x.get_ancestors()), reverse=True)

        return task_typings[0]

    @classmethod
    def call_exporter(
            cls, resource_model_id: str, exporter_typing_name: str, params: ConfigParamsDict) -> ResourceModel:
        # Check that the resource exists
        resource_model = ResourceModel.get_by_id_and_check(resource_model_id)

        # Create an experiment containing 1 source, 1 extractor , 1 sink
        experiment: IExperiment = IExperiment(
            None, title=f"{resource_model.name} exporter", type_=ExperimentType.EXPORTER)
        protocol: IProtocol = experiment.get_protocol()

        # Add the importer and the connector
        exporter_type: Type[ResourceExporter] = TypingManager.get_type_from_name(exporter_typing_name)
        extractor: IProcess = protocol.add_process(exporter_type, 'exporter', params)

        # Add source and connect it,
        protocol.add_source('source', resource_model_id, extractor << 'source')

        # Add sink and connect it, don't flag the resource
        sink = protocol.add_sink('sink', extractor >> 'target', False)

        # run the experiment
        experiment.run(auto_delete_if_error=True)

        # return the resource model of the sink process
        sink.refresh()
        return sink.get_input_resource_model(Sink.input_name)

    ################################################ FILE EXTRACTOR ################################################

    @classmethod
    def call_file_extractor(cls, folder_model_id: str, sub_path: str, fs_node_typing_name: str) -> ResourceModel:
        # Check that the resource exists
        ResourceModel.get_by_id_and_check(folder_model_id)

        # Create an experiment containing 1 source, 1 extractor , 1 sink
        experiment: IExperiment = IExperiment(
            None, title=f"{FileHelper.get_name(sub_path)} extractor", type_=ExperimentType.FS_NODE_EXTRACTOR)
        protocol: IProtocol = experiment.get_protocol()

        # Add the importer and the connector
        extractor: IProcess = protocol.add_process(FsNodeExtractor, 'extractor', {
                                                   'fs_node_path': sub_path, 'fs_node_typing_name': fs_node_typing_name})

        # Add source and connect it
        protocol.add_source('source', folder_model_id, extractor << 'source')

        # Add sink and connect it
        sink = protocol.add_sink('sink', extractor >> 'target')

        #  run the experiment
        experiment.run(auto_delete_if_error=True)

        # return the resource model of the sink process
        sink.refresh()
        return sink.get_input_resource_model(Sink.input_name)

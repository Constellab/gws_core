# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Any, Coroutine, Dict, List, Type

from gws_core.core.model.base import Base
from gws_core.core.utils.utils import Utils
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.file.file_tasks import FsNodeExtractor
from gws_core.impl.file.fs_node import FSNode
from gws_core.resource.resource import Resource
from gws_core.task.converter.exporter import ResourceExporter

from ...config.config_types import ConfigParamsDict
from ...core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ...experiment.experiment import ExperimentType
from ...experiment.experiment_interface import IExperiment
from ...impl.file.file import File
from ...model.typing_manager import TypingManager
from ...process.process_interface import IProcess
from ...protocol.protocol_interface import IProtocol
from ...resource.resource_model import ResourceModel
from ...task.converter.importer import ResourceImporter
from ...task.task_typing import TaskTyping
from .converter_dto import ResourceImportersDTO


class ConverterService:

    ################################################ IMPRTER ################################################

    @classmethod
    def get_importers(cls, resource_typing_name: str, extension: str) -> List[ResourceImportersDTO]:
        """ return the list of importer typing of a resource

        :param resource_typing_name: [description]
        :type resource_typing_name: str
        :return: [description]
        :rtype: List[TaskTyping]
        """
        resource_type: Type[File] = TypingManager.get_type_from_name(resource_typing_name)

        if not Utils.issubclass(resource_type, FSNode):
            raise BadRequestException("The resource must be a FsNode")

        task_typings: List[TaskTyping] = TaskTyping.get_by_related_resource(resource_type, "IMPORTER")

        # Group the importers by resource type
        grouped_tasks: Dict[str, ResourceImportersDTO] = {}
        for task_typing in task_typings:

            # retrieve the task python type
            model_t: Type[Base] = task_typing.get_type()

            # check if the type exist and is a ResourceImporter
            if model_t is None or not issubclass(model_t, ResourceImporter):
                continue

            # Check that the extensions is supported by the importer
            if extension and model_t._supported_extensions and extension not in model_t._supported_extensions:
                continue

            resource_typing: str = task_typing.related_model_typing_name

            # if the resource typing was not added
            if not resource_typing in grouped_tasks:
                grouped_tasks[resource_typing] = ResourceImportersDTO(
                    TypingManager.get_typing_from_name(resource_typing))

            grouped_tasks[resource_typing].add_importer(task_typing)

        # covnert to list and sort it to have the most specific importer first and generic last
        tasks: List[ResourceImportersDTO] = list(grouped_tasks.values())
        tasks.sort(key=lambda x: len(x.resource.get_ancestors()), reverse=True)
        return tasks

    @ classmethod
    async def call_importer(cls, resource_model_id: str, importer_typing_name: str, config: ConfigParamsDict) -> Coroutine[Any, Any, ResourceModel]:
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
        protocol.add_source('source', resource_model_id, importer << 'source')

        # Add sink and connect it
        protocol.add_sink('sink', importer >> 'target')

        # add the experiment to queue to run it
        await experiment.run()

        # return the resource model of the sink process
        return experiment.get_experiment_model().protocol_model.get_process('sink').inputs.get_resource_model('resource')

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
    def call_exporter_directly(
            cls, resource_model_id: str, exporter_typing_name: str, params: ConfigParamsDict) -> FSNode:
        resource_model: ResourceModel = ResourceModel.get_by_id_and_check(resource_model_id)

        resource: Resource = resource_model.get_resource()

        if isinstance(resource, FSNode):
            return resource

        exporter_type: Type[ResourceExporter] = TypingManager.get_type_from_name(exporter_typing_name)

        return exporter_type.call(resource, params)

    ################################################ FILE EXTRACTOR ################################################

    @classmethod
    async def call_file_extractor(cls, folder_model_id: str, sub_path: str, fs_node_typing_name: str) -> ResourceModel:
        # Get and check the resource id
        resource_model: ResourceModel = ResourceModel.get_by_id_and_check(folder_model_id)

        # Create an experiment containing 1 source, 1 extractor , 1 sink
        experiment: IExperiment = IExperiment(
            None, title=f"{FileHelper.get_name(sub_path)} extractor", type_=ExperimentType.EXPERIMENT)
        protocol: IProtocol = experiment.get_protocol()

        # Add the importer and the connector
        extractor: IProcess = protocol.add_process(FsNodeExtractor, 'extractor', {
                                                   'fs_node_path': sub_path, 'fs_node_typing_name': fs_node_typing_name})

        # Add source and connect it
        protocol.add_source('source', folder_model_id, extractor << 'source')

        # Add sink and connect it
        protocol.add_sink('sink', extractor >> 'target')

        # add the experiment to queue to run it
        await experiment.run()

        # return the resource model of the sink process
        return experiment.get_experiment_model().protocol_model.get_process('sink').inputs.get_resource_model('resource')

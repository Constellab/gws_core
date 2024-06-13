

from typing import Type

from peewee import JOIN

from gws_core.core.classes.paginator import Paginator
from gws_core.core.model.model import Model
from gws_core.core.service.external_lab_service import (
    ExternalLabService, ExternalLabWithUserInfo)
from gws_core.core.utils.logger import Logger
from gws_core.experiment.experiment_interface import IExperiment
from gws_core.impl.file.file import File
from gws_core.model.typing_manager import TypingManager
from gws_core.process.process_interface import IProcess
from gws_core.process.process_types import ProcessStatus
from gws_core.protocol.protocol_interface import IProtocol
from gws_core.resource.resource import Resource
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.resource_set.resource_list_base import ResourceListBase
from gws_core.resource.resource_zipper_task import ResourceZipperTask
from gws_core.share.share_link_service import ShareLinkService
from gws_core.share.shared_dto import (SharedEntityMode,
                                       ShareEntityInfoReponseDTO,
                                       ShareEntityZippedResponseDTO,
                                       ShareLinkType)
from gws_core.share.shared_entity_info import SharedEntityInfo
from gws_core.share.shared_resource import SharedResource
from gws_core.task.plug import Sink
from gws_core.task.task_input_model import TaskInputModel
from gws_core.task.task_model import TaskModel
from gws_core.user.current_user_service import AuthenticateUser
from gws_core.user.user import User

from .share_link import ShareLink


class ShareService():
    """Service to manage communication between lab to share entities
    """

    # version of the share service
    VERSION = 2

    @classmethod
    def get_shared_to_list(
            cls, entity_type: ShareLinkType, entity_id: str,
            page: int = 0, number_of_items_per_page: int = 20) -> Paginator[SharedEntityInfo]:
        """Retrun the list of lab that downloaded the resource
        """

        share_entity_info: Type[SharedEntityInfo] = cls._get_shared_entity_type(entity_type)

        query = share_entity_info.get_sents(entity_id)

        paginator: Paginator[ShareLink] = Paginator(
            query, page=page, nb_of_items_per_page=number_of_items_per_page)
        return paginator

    @classmethod
    def mark_entity_as_shared(cls, entity_type: ShareLinkType,
                              token: str, receiver_lab: ExternalLabWithUserInfo) -> None:
        """Method called by an external lab after the an entity was successfully
        import in the external lab. This helps this lab to keep track of which lab downloaded the entity
        """
        shared_entity_link: ShareLink = ShareLinkService.find_by_token_and_check(token)

        share_entity_info: Type[SharedEntityInfo] = cls._get_shared_entity_type(entity_type)

        # check if this resource was already downloaded by this lab
        if share_entity_info.already_shared_with_lab(shared_entity_link.entity_id, receiver_lab.lab_id):
            return

        share_entity_info.create_from_lab_info(shared_entity_link.entity_id, SharedEntityMode.SENT,
                                               receiver_lab, shared_entity_link.created_by)

    @classmethod
    def _get_shared_entity_type(cls, entity_type: ShareLinkType) -> Type[SharedEntityInfo]:
        """Return the shared entity type
        """
        if entity_type == ShareLinkType.RESOURCE:
            return SharedResource
        else:
            raise Exception(f'Entity type {entity_type} is not supported')

    @classmethod
    def get_share_entity_info(cls, token: str) -> ShareEntityInfoReponseDTO:
        shared_entity_link: ShareLink = ShareLinkService.find_by_token_and_check_validity(
            token)

        model: Model = shared_entity_link.get_model_and_check(
            shared_entity_link.entity_id, shared_entity_link.entity_type)

        entity_object: list = None
        if isinstance(model, ResourceModel):
            entity_object = [model.to_dto()]

            # specific case for resource set that contains multiple resource
            # we need to add all the resource to the zip
            resource = model.get_resource()
            if isinstance(resource, ResourceListBase):
                resource_models = resource.get_resource_models()
                entity_object.extend([resource_model.to_dto() for resource_model in resource_models])
        else:
            raise Exception(f'Entity type {shared_entity_link.entity_type} is not supported')

        zip_url: str = ExternalLabService.get_current_lab_route(f"share/zip-entity/{token}")
        return ShareEntityInfoReponseDTO(version=cls.VERSION, entity_type=shared_entity_link.entity_type,
                                         entity_id=shared_entity_link.entity_id, entity_object=entity_object,
                                         zip_entity_route=zip_url)

    @classmethod
    def zip_shared_entity(cls, token: str) -> ShareEntityZippedResponseDTO:
        shared_entity_link: ShareLink = ShareLinkService.find_by_token_and_check(token)

        zipped_resource: ResourceModel
        if shared_entity_link.entity_type == ShareLinkType.RESOURCE:
            zipped_resource = cls.zip_shared_resource(shared_entity_link)
        else:
            raise Exception(f'Entity type {shared_entity_link.entity_type} is not supported')

        # generate the link to download the zipped resource
        download_url: str = ExternalLabService.get_current_lab_route(f"share/download/{token}/{zipped_resource.id}")
        return ShareEntityZippedResponseDTO(
            version=cls.VERSION, entity_type=shared_entity_link.entity_type, entity_id=shared_entity_link.entity_id,
            zipped_entity_resource_id=zipped_resource.id, download_entity_route=download_url)

    @classmethod
    def download_zipped_entity(cls, token: str, zipped_entity_id: str) -> str:
        """Method that is used to download the zipped resource generated by the shared action
        """

        shared_entity_link: ShareLink = ShareLinkService.find_by_token_and_check_validity(token)

        shared_entity: Model = shared_entity_link.get_model_and_check(
            shared_entity_link.entity_id, shared_entity_link.entity_type)

        # retrieve the zipped resource that contains the shared entity
        zipped_resource: ResourceModel = ResourceModel.get_by_id_and_check(zipped_entity_id)
        zip_file: Resource = zipped_resource.get_resource()

        if not isinstance(zip_file, File):
            raise Exception('Zip file is not a file')

        # check that the generated zip resource was generated from the shared entity of the token
        if zip_file.get_technical_info('origin_entity_id').value != shared_entity.id:
            raise Exception('Zip file does not contain the shared entity')

        return zip_file.path

    #################################### RESOURCE ####################################

    @classmethod
    def zip_shared_resource(cls, shared_entity_link: ShareLink) -> ResourceModel:
        # check if the resource was already zipped in this lab for the current version of ResourceZipperTask
        typing = TypingManager.get_typing_from_name_and_check(ResourceZipperTask._typing_name)
        task_model: TaskModel = TaskModel.select().where(
            (TaskModel.process_typing_name == typing.typing_name) &
            (TaskModel.status == ProcessStatus.SUCCESS) &
            (TaskModel.brick_version_on_run == typing.brick_version) &
            (TaskInputModel.resource_model == shared_entity_link.entity_id)) \
            .join(TaskInputModel, JOIN.LEFT_OUTER) \
            .first()

        # if the resource was already zipped
        if task_model:
            Logger.info(
                f"Resource {shared_entity_link.entity_id} was already zipped by task {task_model.id}, using the same zip file.")
            return task_model.outputs.get_resource_model(ResourceZipperTask.output_name)

        with AuthenticateUser(shared_entity_link.created_by):
            return cls.run_zip_resource_exp(shared_entity_link.entity_id, shared_entity_link.created_by)

    @classmethod
    def run_zip_resource_exp(cls, id_: str, shared_by: User) -> ResourceModel:
        """Method that zip a resource ands return the new resource
        """

        resource_model: ResourceModel = ResourceModel.get_by_id_and_check(id_)

        experiment: IExperiment = IExperiment(
            None, title=f"{resource_model.name} zipper")
        protocol: IProtocol = experiment.get_protocol()

        # Add the importer and the connector
        zipper: IProcess = protocol.add_process(ResourceZipperTask, 'zipper', {'shared_by_id': shared_by.id})

        # Add source and connect it
        protocol.add_source('source', resource_model.id, zipper << ResourceZipperTask.input_name)

        # Add sink and connect it
        sink = protocol.add_sink('sink', zipper >> ResourceZipperTask.output_name, False)

        experiment.run(auto_delete_if_error=True)
        sink.refresh()

        return sink.get_input_resource_model(Sink.input_name)

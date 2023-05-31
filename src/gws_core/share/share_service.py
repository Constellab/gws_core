# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Type

from gws_core.core.classes.paginator import Paginator
from gws_core.core.service.external_lab_service import ExternalLabWithUserInfo
from gws_core.experiment.experiment_enums import ExperimentType
from gws_core.experiment.experiment_interface import IExperiment
from gws_core.process.process_interface import IProcess
from gws_core.protocol.protocol_interface import IProtocol
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.resource_zipper import ResourceZipper
from gws_core.share.resource_downloader_http import ResourceDownloaderHttp
from gws_core.share.share_link_service import ShareLinkService
from gws_core.share.shared_entity_info import (SharedEntityInfo,
                                               SharedEntityMode)
from gws_core.share.shared_resource import SharedResource
from gws_core.task.plug import Sink
from gws_core.user.user import User

from .share_link import ShareLink, ShareLinkType


class ShareService():
    """Service to manage communication between lab to share entities
    """

    @classmethod
    def get_shared_to_list(
            cls, entity_type: ShareLinkType, entity_id: str,
            page: int = 0, number_of_items_per_page: int = 20) -> Paginator[SharedEntityInfo]:
        """Retrun the list of lab that downloaded the resource
        """

        entity_type: Type[SharedEntityInfo] = cls._get_shared_entity_type(
            entity_type)

        query = entity_type.get_sents(entity_id)

        paginator: Paginator[ShareLink] = Paginator(
            query, page=page, nb_of_items_per_page=number_of_items_per_page)
        return paginator

    @classmethod
    def mark_entity_as_shared(cls, entity_type: ShareLinkType,
                              token: str, receiver_lab: ExternalLabWithUserInfo) -> None:
        """Method called by an external lab after the an entity was successfully
        import in the external lab. This helps this lab to keep track of which lab downloaded the entity
        """
        shared_entity_link: ShareLink = ShareLinkService.find_by_token_and_check(
            token)

        entity_type: Type[SharedEntityInfo] = cls._get_shared_entity_type(
            entity_type)

        # check if this resource was already downloaded by this lab
        if entity_type.already_shared_with_lab(shared_entity_link.entity_id, receiver_lab['lab_id']):
            return

        cls._create_shared_entity(entity_type, shared_entity_link.entity_id,  SharedEntityMode.SENT, receiver_lab,
                                  shared_entity_link.created_by)

    @classmethod
    def _get_shared_entity_type(cls, entity_type: ShareLinkType) -> Type[SharedEntityInfo]:
        """Return the shared entity type
        """
        if entity_type == ShareLinkType.RESOURCE:
            return SharedResource
        else:
            raise Exception(f'Entity type {entity_type} is not supported')

    #################################### RESOURCE ####################################

    @classmethod
    def zip_resource_from_token(cls, token: str) -> str:
        """Method that zip a resource and return the file path
        """

        shared_entity_link: ShareLink = ShareLinkService.find_by_token_and_check_validity(
            token)

        return cls.zip_resource(shared_entity_link.entity_id, shared_entity_link.created_by)

    @classmethod
    def zip_resource(cls, id: str, shared_by: User) -> str:
        """Method that zip a resource and return the file path
        """

        resource_zipper = ResourceZipper(shared_by)

        resource_zipper.add_resource_model(id)

        resource_zipper.close_zip()

        return resource_zipper.get_zip_file_path()

    @classmethod
    def download_resource_from_external_lab(cls, link: str) -> ResourceModel:
        # Create an experiment containing 1 resource downloader , 1 sink
        experiment: IExperiment = IExperiment(
            None, title="Resource downloader", type_=ExperimentType.RESOURCE_DOWNLOADER)
        protocol: IProtocol = experiment.get_protocol()

        # Add the importer and the connector
        importer: IProcess = protocol.add_process(ResourceDownloaderHttp, 'downloader', {
            ResourceDownloaderHttp.config_name: link
        })

        # Add sink and connect it
        protocol.add_sink('sink', importer >> 'resource')

        # run the experiment
        try:
            experiment.run()
        except Exception as exception:
            if not experiment.is_running():
                # delete experiment if there was an error
                experiment.delete()
            raise exception

        # return the resource model of the sink process
        return experiment.get_experiment_model().protocol_model.get_process('sink').inputs.get_resource_model(Sink.input_name)

    @classmethod
    def _create_shared_entity(cls, shared_entity_type: Type[SharedEntityInfo], entity_id: str,
                              mode: SharedEntityMode, lab_info: ExternalLabWithUserInfo, created_by: User) -> None:
        """Method that log the resource origin for each imported resources
        """

        shared_entity = shared_entity_type()
        shared_entity.entity = entity_id
        shared_entity.share_mode = mode
        shared_entity.lab_id = lab_info['lab_id']
        shared_entity.lab_name = lab_info['lab_name']
        shared_entity.user_id = lab_info['user_id']
        shared_entity.user_firstname = lab_info['user_firstname']
        shared_entity.user_lastname = lab_info['user_lastname']
        shared_entity.space_id = lab_info['space_id']
        shared_entity.space_name = lab_info['space_name']
        shared_entity.created_by = created_by
        shared_entity.save()

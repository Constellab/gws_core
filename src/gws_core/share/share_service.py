# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import os
from typing import Type

from requests.models import Response

from gws_core.core.classes.paginator import Paginator
from gws_core.core.decorator.transaction import transaction
from gws_core.core.service.external_lab_service import (
    ExternalLabService, ExternalLabWithUserInfo)
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.resource_zipper import ResourceUnzipper, ResourceZipper
from gws_core.share.share_link_service import ShareLinkService
from gws_core.share.shared_entity_info import (SharedEntityInfo,
                                               SharedEntityMode)
from gws_core.share.shared_resource import SharedResource
from gws_core.user.current_user_service import CurrentUserService
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

        entity_type: Type[SharedEntityInfo] = cls._get_shared_entity_type(entity_type)

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
        shared_entity_link: ShareLink = ShareLinkService.find_by_token_and_check(token)

        entity_type: Type[SharedEntityInfo] = cls._get_shared_entity_type(entity_type)

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
    def download_resource_from_token(cls, token: str) -> str:
        """Method that zip a resource and return the file
        """

        shared_entity_link: ShareLink = ShareLinkService.find_by_token_and_check_validity(token)

        return cls.download_resource(
            shared_entity_link.entity_id, shared_entity_link.created_by)

    @classmethod
    def download_resource(cls, id: str, shared_by: User) -> str:
        """Method that zip a resource and return the file
        """

        resource_zipper = ResourceZipper(shared_by)

        resource_zipper.add_resource(id)

        resource_zipper.close_zip()

        return resource_zipper.get_zip_file_path()

    @classmethod
    def create_resource_from_external_lab(cls, link: str) -> ResourceModel:
        """Method that copy an external resource
        """

        # retrieve the token which is the last part of the link
        share_token = link.split('/')[-1]

        response: Response = ExternalLabService.get_shared_object(link)

        # create a temp dir
        temp_dir = Settings.get_instance().make_temp_dir()
        zip_file = os.path.join(temp_dir, 'resource.zip')

        # write the response to a file
        with open(zip_file, "wb") as f:
            f.write(response.content)

        return cls.create_resource_from_external_lab_zip(zip_file, share_token)

    @classmethod
    def create_resource_from_external_lab_zip(cls, zip_path: str, share_token: str) -> ResourceModel:

        resource_unzipper = cls.create_resource_from_zip(zip_path)

        # call the origin lab to mark the resource as received
        current_lab_info = ExternalLabService.get_current_lab_info(CurrentUserService.get_and_check_current_user())
        response: Response = ExternalLabService.mark_shared_object_as_received(
            resource_unzipper.get_origin_info()['lab_api_url'],
            ShareLinkType.RESOURCE, share_token, current_lab_info)

        if response.status_code != 200:
            Logger.error("Error while marking the resource as received: " + response.text)

        return resource_unzipper.resource_models[0]

    @classmethod
    @transaction()
    def create_resource_from_zip(cls, zip_path: str) -> ResourceUnzipper:

        resource_unzipper = ResourceUnzipper(zip_path)

        try:

            resource_unzipper.load_resources()
            resource_unzipper.save_all_resources()

            # for each new resource, create a shared resource to store the origin info
            for resource_model in resource_unzipper.resource_models:
                cls._create_shared_entity(SharedResource, resource_model.id, SharedEntityMode.RECEIVED,
                                          resource_unzipper.get_origin_info(),
                                          CurrentUserService.get_and_check_current_user())
            return resource_unzipper
        except Exception as err:
            # clean the resource models
            for resource_model in resource_unzipper.resource_models:
                resource_model.delete_object()

            raise err

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

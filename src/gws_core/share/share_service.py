# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import os
from typing import List, Optional

from requests.models import Response

from gws_core.core.classes.paginator import Paginator
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.model.model import Model
from gws_core.core.service.external_lab_service import ExternalLabService
from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.core.utils.string_helper import StringHelper
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.resource_zipper import (ResourceUnzipper,
                                               ResourceZipper, ZipOriginInfo)
from gws_core.share.shared_resource import SharedResource, SharedResourceMode
from gws_core.user.current_user_service import CurrentUserService
from gws_core.user.user import User

from .shared_dto import GenerateShareLinkDTO
from .shared_entity import SharedEntityLink, SharedEntityLinkType


class ShareService():

    @classmethod
    def find_by_entity_id_and_type(
            cls, entity_type: str, entity_id: SharedEntityLinkType) -> Optional[SharedEntityLink]:
        """Method that find a shared entity link by its entity id and type
        """

        return SharedEntityLink.find_by_entity_type_and_id(entity_type, entity_id)

    @classmethod
    def generate_share_link(cls, share_dto: GenerateShareLinkDTO) -> SharedEntityLink:
        """Method that generate a share link for a given entity
        """

        existing_link: SharedEntityLink = SharedEntityLink.find_by_entity_type_and_id(
            entity_type=share_dto.entity_type, entity_id=share_dto.entity_id)

        if existing_link:
            raise BadRequestException("Share link already exists for this object")

        model: Model = SharedEntityLink.get_model_and_check(share_dto.entity_id, share_dto.entity_type)

        shared_link_model = SharedEntityLink()
        shared_link_model.entity_id = model.id
        shared_link_model.entity_type = share_dto.entity_type
        shared_link_model.valid_until = share_dto.valid_until
        shared_link_model.token = StringHelper.generate_uuid() + '_' + str(DateHelper.now_utc_as_milliseconds())

        return shared_link_model.save()

    @classmethod
    def update_share_link(cls, share_dto: GenerateShareLinkDTO) -> SharedEntityLink:
        """Method that update a share link for a given entity
        """

        shared_entity_link: SharedEntityLink = SharedEntityLink.find_by_entity_type_and_id_and_check(
            share_dto.entity_type, share_dto.entity_id)

        shared_entity_link.valid_until = share_dto.valid_until
        return shared_entity_link.save()

    @classmethod
    def delete_share_link(cls, id: str) -> None:
        """Method that delete a share link for a given entity
        """

        SharedEntityLink.delete_by_id(id)

    @classmethod
    def get_shared_links(cls, page: int = 0, number_of_items_per_page: int = 20) -> Paginator[SharedEntityLink]:
        """Method that return the shared links
        """

        query = SharedEntityLink.select().order_by(SharedEntityLink.valid_until.asc())

        paginator: Paginator[SharedEntityLink] = Paginator(
            query, page=page, nb_of_items_per_page=number_of_items_per_page)
        return paginator

    @classmethod
    def download_resource_from_token(cls, token: str) -> str:
        """Method that download a resource
        """

        shared_entity_link: SharedEntityLink = SharedEntityLink.find_by_token_and_check(token)

        return cls.download_resource(
            shared_entity_link.entity_id, shared_entity_link.created_by)

    @classmethod
    def download_resource(cls, id: str, shared_by: User) -> str:
        """Method that download a resource
        """

        resource_zipper = ResourceZipper(shared_by)

        resource_zipper.add_resource(id)

        resource_zipper.close_zip()

        return resource_zipper.get_zip_file_path()

    @classmethod
    def mark_resource_as_downloaded(cls, token: str, receiver: ZipOriginInfo) -> None:
        """Method called by an external lab after the resource was successfully
        import in the external lab. This helps this lab to keep track of which lab downloaded the resource
        """
        shared_entity_link: SharedEntityLink = SharedEntityLink.find_by_token_and_check(token)

        # check if this resource was already downloaded by this lab
        shared_resource = SharedResource.get_or_none(
            SharedResource.resource == shared_entity_link.entity_id, SharedResource.share_mode == SharedResourceMode.SENT,
            SharedResource.lab_id == receiver['lab_id'])

        if shared_resource:
            return

        cls._create_shared_resource(shared_entity_link.entity_id,  SharedResourceMode.SENT, receiver)

    @classmethod
    def copy_external_resource(cls, link: str) -> ResourceModel:
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

        return cls.copy_resource_from_zip(zip_file, share_token)

    @classmethod
    def copy_resource_from_zip(cls, zip_path: str, share_token: str) -> ResourceModel:

        resource_unzipper = cls.copy_resource_from_zip_2(zip_path)

        # call the origin lab to mark the resource as received
        current_lab_info = ResourceZipper.generate_origin(CurrentUserService.get_and_check_current_user())
        response: Response = ExternalLabService.mark_shared_object_as_received(
            resource_unzipper.get_origin_info()['lab_api_url'], share_token, current_lab_info)

        if response.status_code != 200:
            Logger.error("Error while marking the resource as received: " + response.text)

        return resource_unzipper.resource_models[0]

    @classmethod
    def copy_resource_from_zip_2(cls, zip_path: str) -> ResourceUnzipper:

        resource_unzipper = ResourceUnzipper(zip_path)

        resource_unzipper.load_resources()
        resource_unzipper.save_all_resources()

        # for each new resource, create a shared resource to store the origin info
        for resource_model in resource_unzipper.resource_models:
            cls._create_shared_resource(resource_model.id, SharedResourceMode.RECEIVED,
                                        resource_unzipper.get_origin_info())
        return resource_unzipper

    @classmethod
    def _create_shared_resource(cls, resource_id: str, mode: SharedResourceMode, origin_info: ZipOriginInfo) -> None:
        """Method that log the resource origin for each imported resources
        """

        shared_resource = SharedResource()
        shared_resource.resource = resource_id
        shared_resource.share_mode = mode
        shared_resource.lab_id = origin_info['lab_id']
        shared_resource.lab_name = origin_info['lab_name']
        shared_resource.user_id = origin_info['user_id']
        shared_resource.user_firstname = origin_info['user_firstname']
        shared_resource.user_lastname = origin_info['user_lastname']
        shared_resource.space_id = origin_info['space_id']
        shared_resource.space_name = origin_info['space_name']
        shared_resource.save()

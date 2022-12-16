# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import os
from typing import List

from fastapi.responses import FileResponse
from requests.models import Response

from gws_core.core.classes.paginator import Paginator
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.model.model import Model
from gws_core.core.service.external_api_service import ExternalApiService
from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.settings import Settings
from gws_core.core.utils.string_helper import StringHelper
from gws_core.impl.file.file_helper import FileHelper
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.resource_zip_service import ResourceZipService

from .shared_dto import GenerateShareLinkDTO
from .shared_entity import SharedEntityLink


class ShareService():

    @classmethod
    def generate_share_link(cls, share_dto: GenerateShareLinkDTO) -> SharedEntityLink:
        """Method that generate a share link for a given entity
        """

        existing_link: SharedEntityLink = SharedEntityLink.find_by_entity_id_and_type(
            entity_id=share_dto.entity_id, entity_type=share_dto.entity_type)

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

        shared_entity_link: SharedEntityLink = SharedEntityLink.find_by_entity_id_and_type_and_check(
            share_dto.entity_id, share_dto.entity_type)

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
    def download_resource(cls, token: str) -> FileResponse:
        """Method that download a resource
        """

        shared_entity_link: SharedEntityLink = SharedEntityLink.find_by_token_and_check(token)

        zip_path: str = ResourceZipService.download_complete_resource(
            shared_entity_link.entity_id, shared_entity_link.created_by)

        return FileResponse(zip_path, media_type=FileHelper.get_mime(zip_path),
                            filename=FileHelper.get_name_with_extension(zip_path))

    @classmethod
    def copy_external_resource(cls, link: str) -> ResourceModel:
        """Method that copy an external resource
        """

        response: Response = ExternalApiService.get(link)

        # create a temp dir
        temp_dir = Settings.get_instance().make_temp_dir()
        zip_file = os.path.join(temp_dir, 'resource.zip')

        # write the response to a file
        with open(zip_file, "wb") as f:
            f.write(response.content)

        resource_models: List[ResourceModel] = ResourceZipService.import_resource_from_zip(zip_file)

        return resource_models[0]

# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import List

from gws_core.resource.resource_model import ResourceModel
from gws_core.share.shared_resource import SharedResource, SharedResourceMode
from gws_core.user.user import User

from .resource_zipper import ResourceUnzipper, ResourceZipper


class ResourceZipService():

    @classmethod
    def download_complete_resource(cls, id: str, shared_by: User) -> str:
        resource_zipper = ResourceZipper(shared_by)

        resource_zipper.add_resource(id)

        resource_zipper.close_zip()

        return resource_zipper.get_zip_file_path()

    @classmethod
    def import_resource_from_zip(cls, zip_file: str) -> List[ResourceModel]:

        resource_unzipper = ResourceUnzipper(zip_file)

        resource_unzipper.load_resources()
        resource_unzipper.save_all_resources()
        cls._create_shared_resource(resource_unzipper)

        return resource_unzipper.resource_models

    @classmethod
    def _create_shared_resource(cls, resource_unzipper: ResourceUnzipper) -> None:
        """Method that log the resource origin for each imported resources
        """

        origin_info = resource_unzipper.get_origin_info()

        for resource_model in resource_unzipper.resource_models:
            shared_resource = SharedResource()
            shared_resource.resource = resource_model
            shared_resource.share_mode = SharedResourceMode.RECEIVED
            shared_resource.lab_id = origin_info['lab_id']
            shared_resource.lab_name = origin_info['lab_name']
            shared_resource.user_id = origin_info['user_id']
            shared_resource.user_firstname = origin_info['user_firstname']
            shared_resource.user_lastname = origin_info['user_lastname']
            shared_resource.space_id = origin_info['space_id']
            shared_resource.space_name = origin_info['space_name']
            shared_resource.save()

# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import List

from .resource_model import ResourceModel
from .resource_zipper import ResourceUnzipper, ResourceZipper


class ResourceZipService():

    @classmethod
    def download_complete_resource(cls, id: str) -> str:
        resource_zipper = ResourceZipper()

        resource_zipper.add_resource(id)

        resource_zipper.close_zip()

        return resource_zipper.get_zip_file_path()

    @classmethod
    def import_resource_from_zip(cls, zip_file: str) -> List[ResourceModel]:

        resource_unzipper = ResourceUnzipper(zip_file)

        resource_unzipper.load_resources()

        return resource_unzipper.save_all_resources()

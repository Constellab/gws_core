# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from json import load
from typing import Dict, List, Type

from gws_core.brick.brick_helper import BrickHelper
from gws_core.core.service.external_lab_service import ExternalLabWithUserInfo
from gws_core.core.utils.compress.compress import Compress
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file import File
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.file.folder import Folder
from gws_core.impl.file.fs_node import FSNode
from gws_core.model.typing import TypingNameObj
from gws_core.model.typing_manager import TypingManager
from gws_core.resource.kv_store import KVStore
from gws_core.resource.resource import Resource
from gws_core.resource.resource_factory import ResourceFactory
from gws_core.resource.resource_set.resource_set import ResourceSet

from .resource_zipper import ResourceZipper, ZipResource, ZipResourceInfo


class ResourceLoader():
    """ Class to load a resource from a folder"""

    info_json: ZipResourceInfo

    resource_folder: str

    resource: Resource
    children_resources: List[Resource]

    def __init__(self, resource_folder: str) -> None:
        self.info_json = None
        self.resource_folder = resource_folder
        self.children_resources = []

    def is_resource_zip(self) -> bool:
        """Return true if the zip file is a resource zip file
        """
        try:
            self._load_info_json()
            return True
        except Exception:
            return False

    def load_resource(self) -> Resource:

        if not self.is_resource_zip():
            return self._load_fs_node_resource()

        self._check_compatibility()

        main_resource = self.get_main_resource()
        self.resource = self._load_resource(main_resource)

        if isinstance(self.resource, ResourceSet):

            # Get the resource ids from the ResourceSet
            resource_ids: Dict[str, str] = self.resource._resource_ids
            # invserse the dict to be able to retrieve resource name from id
            resource_names: Dict[str, str] = {}
            for key, value in resource_ids.items():
                resource_names[value] = key

            # remove all the resources from the ResourceSet to add the new ones
            self.resource.clear_resources()

            for zip_resource in self.get_children_resources():
                resource: Resource = self._load_resource(zip_resource)

                # retrieve the name of the resource from the id in the resource set
                resource_name = resource_names[zip_resource['id']]
                self.resource.add_resource(resource, unique_name=resource_name)

                self.children_resources.append(resource)

        return self.resource

    def _check_compatibility(self) -> None:
        if self.info_json['zip_version'] != 1:
            raise Exception(
                f'Zip version {self.info_json["zip_version"]} is not supported.')

        for zip_resource in self.get_all_resources():
            typing = TypingNameObj.from_typing_name(
                zip_resource['resource_typing_name'])

            if not BrickHelper.brick_is_loaded(typing.brick_name):
                raise Exception(f'Brick {typing.brick_name} is not loaded.')

            # check that the type exist
            TypingManager.get_typing_from_name_and_check(
                zip_resource['resource_typing_name'])

    def _load_resource(self, zip_resource: ZipResource) -> Resource:
        # create the kvstore
        kv_store: KVStore = None
        if zip_resource.get('kvstore_dir_name') is not None:
            # build the path to the kvstore file
            kvstore_path = os.path.join(
                self.resource_folder, zip_resource['kvstore_dir_name'], KVStore.FILE_NAME)

            kv_store = KVStore(kvstore_path)

        resource_type: Type[Resource] = TypingManager.get_type_from_name(
            zip_resource['resource_typing_name'])

        resource = ResourceFactory.create_resource(resource_type, kv_store=kv_store, data=zip_resource['data'],
                                                   name=zip_resource['name'])

        # generate a new uid for the resource
        resource.uid = Resource.uid.get_default_value()

        # if the resource is an fs_node_name
        if zip_resource.get('fs_node_name') is not None:
            if not isinstance(resource, FSNode):
                raise Exception('Resource type is not a FSNode')

            # set the path of the resource node
            resource.path = os.path.join(
                self.resource_folder, zip_resource['fs_node_name'])
            # clear other values
            resource.file_store_id = None
            resource.is_symbolic_link = False

        return resource

    def _load_info_json(self) -> ZipResourceInfo:
        if self.info_json is not None:
            return self.info_json

        info_json_path = os.path.join(
            self.resource_folder, ResourceZipper.INFO_JSON_FILE_NAME)

        if not FileHelper.exists_on_os(info_json_path):
            raise Exception(
                f'File {info_json_path} not found in the zip file.')

        info_json: ZipResourceInfo = None
        with open(info_json_path, 'r', encoding='UTF-8') as file:
            info_json = load(file)

        if info_json is None:
            raise Exception(f'File {info_json_path} is empty.')

        if not isinstance(info_json.get('zip_version'), int):
            raise Exception(
                f"The zip_version value '{info_json.get('zip_version')}' in {info_json_path} file is invalid, must be an int")

        if info_json.get('resource') is None:
            raise Exception(
                f"The resource in {info_json_path} is missing")

        if not isinstance(info_json.get('children_resources'), list):
            raise Exception(
                f"The children_resources value in {info_json_path} file is invalid, must be a list")

        self.info_json = info_json

        return self.info_json

    def _load_fs_node_resource(self) -> FSNode:
        """Load the File or Folder resource from folder if the folder
        is not a resource export but only files.
        If there is 1 file or folder in the folder, return it.
        If there is more than 1 file in the folder, return the folder.
        """
        # count the files and folders directly in the result folder
        count = len(os.listdir(self.resource_folder))

        if count == 0:
            raise Exception(
                "The zipped file does not contains any resource.")

        if count == 1:
            node_name = os.listdir(self.resource_folder)[0]
            sub_path = os.path.join(self.resource_folder, node_name)
            if os.path.isdir(sub_path):
                return Folder(sub_path)
            else:
                return File(sub_path)
        else:
            # if there is more than 1 file or folder, return a Folder
            return Folder(self.resource_folder)

    def get_origin_info(self) -> ExternalLabWithUserInfo:
        return self.info_json['origin']

    def get_main_resource(self) -> ZipResource:
        return self.info_json['resource']

    def get_children_resources(self) -> List[ZipResource]:
        return self.info_json['children_resources']

    def get_all_resources(self) -> List[ZipResource]:
        return [self.get_main_resource()] + self.get_children_resources()

    def get_all_generated_resources(self) -> List[Resource]:
        return [self.resource] + self.children_resources

    def delete_resource_folder(self) -> None:
        FileHelper.delete_dir(self.resource_folder)

    @classmethod
    def from_compress_file(cls, compress_file_path: str) -> 'ResourceLoader':
        """Uncompress a file and create a ResourceLoader
        """
        temp_dir = Settings.get_instance().make_temp_dir()
        Compress.smart_decompress(compress_file_path, temp_dir)
        return ResourceLoader(temp_dir)

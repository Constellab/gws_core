# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from json import dump, load
from typing import Dict, List, Optional, Type
from zipfile import ZipFile

from typing_extensions import TypedDict

from gws_core.brick.brick_helper import BrickHelper
from gws_core.core.service.external_lab_service import (
    ExternalLabService, ExternalLabWithUserInfo)
from gws_core.core.utils.compress.compress import Compress
from gws_core.core.utils.compress.zip import Zip
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file import File
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.file.folder import Folder
from gws_core.impl.file.fs_node import FSNode
from gws_core.impl.file.fs_node_model import FSNodeModel
from gws_core.model.typing import TypingNameObj
from gws_core.model.typing_manager import TypingManager
from gws_core.resource.kv_store import KVStore
from gws_core.resource.resource import Resource
from gws_core.resource.resource_factory import ResourceFactory
from gws_core.resource.resource_set.resource_list_base import ResourceListBase
from gws_core.resource.resource_set.resource_set import ResourceSet
from gws_core.user.user import User

from .resource_model import ResourceModel
from .resource_service import ResourceService


class ZipResource(TypedDict):
    id: str
    name: str
    resource_typing_name: str
    brick_version: str
    data: dict
    parent_resource_id: str
    kvstore_dir_name: Optional[str]

    # Name of the file or directory if the resource is a FsNode
    fs_node_name: Optional[str]


class ZipResourceInfo(TypedDict):
    """ Content of the info.json file in the zip file when a resource is zipped"""
    zip_version: int
    # TODO : deprecated, remove when all lab are v0.5.0
    resources: Optional[List[ZipResource]]
    resource: ZipResource
    children_resources: List[ZipResource]
    origin: ExternalLabWithUserInfo


class ResourceZipper():
    """ Class to generate a zip file containing everythinga needed to recreate a resource"""

    ZIP_FILE_NAME = 'resource.zip'
    KV_STORE_FILE_NAME = 'kvstore'
    FS_NODE_FILE_NAME = 'filestore'
    INFO_JSON_FILE_NAME = 'info.json'
    COMPRESS_EXTENSION = 'zip'

    temp_dir: str

    zip: Zip

    resource_info: ZipResourceInfo

    shared_by: User

    def __init__(self, shared_by: User):
        self.shared_by = shared_by
        self.temp_dir = Settings.get_instance().make_temp_dir()
        self.zip = Zip(self.get_zip_file_path())
        self.resource_info = {
            'zip_version': 1,
            'resource': None,
            'children_resources': [],
            'origin': ExternalLabService.get_current_lab_info(self.shared_by)
        }

    def add_resource(self, resource: Resource) -> None:
        self.add_resource_model(resource._model_id)

    def add_resource_model(self, resource_id: str, parent_resource_id: str = None) -> None:

        resource_model: ResourceModel = ResourceService.get_resource_by_id(
            resource_id)

        resource_zip: ZipResource = {
            'id': resource_model.id,
            'name': resource_model.name,
            'resource_typing_name': resource_model.resource_typing_name,
            'brick_version': resource_model.brick_version,
            'data': resource_model.data,
            'parent_resource_id': parent_resource_id,
            'kvstore_dir_name': None,
            'fs_node_name': None
        }

        resource_index = self._get_next_resource_index()

        # add the kvstore
        kvstore: KVStore = resource_model.get_kv_store()
        if kvstore is not None:
            kvstore_file_name = f'{self.KV_STORE_FILE_NAME}_{resource_index}'
            # add the kvstore folder in the zip and name this folder kvstore
            self.zip.add_dir(kvstore.full_file_dir, dir_name=kvstore_file_name)
            resource_zip['kvstore_dir_name'] = kvstore_file_name

        # add the fs_node
        fs_node_model: FSNodeModel = resource_model.fs_node_model
        if fs_node_model is not None:
            if FileHelper.is_dir(fs_node_model.path):
                fs_node_file_name = f'{self.FS_NODE_FILE_NAME}_{resource_index}'
            else:
                fs_node_file_name = f'{self.FS_NODE_FILE_NAME}_{resource_index}.{FileHelper.get_extension(fs_node_model.path)}'

            self.zip.add_fs_node(fs_node_model.path,
                                 fs_node_name=fs_node_file_name)
            resource_zip['fs_node_name'] = fs_node_file_name

        # add the resource info
        if parent_resource_id is None:
            self.resource_info['resource'] = resource_zip
        else:
            self.resource_info['children_resources'].append(resource_zip)

        # if the resource is a ResourceListBase, add all the children to the zip recursively
        resource: Resource = resource_model.get_resource()
        if isinstance(resource, ResourceListBase) and not isinstance(resource, ResourceSet):
            raise Exception(
                'Only ResourceSet is supported other sub class of ResourceListBase are not supported yet.')

        if isinstance(resource, ResourceSet):
            for child_resource in resource.get_resources_as_set():
                self.add_resource_model(child_resource._model_id, resource_id)

    def _get_next_resource_index(self) -> int:
        return len(self.resource_info['children_resources'])\
            + (0 if self.resource_info['resource'] is None else 1)

    def get_zip_file_path(self):
        return os.path.join(self.temp_dir, self.ZIP_FILE_NAME)

    def close_zip(self) -> str:
        # add the info.json file
        info_json = os.path.join(self.temp_dir, self.INFO_JSON_FILE_NAME)
        with open(info_json, 'w', encoding='UTF-8') as file:
            dump(self.resource_info, file)

        self.zip.add_file(info_json, file_name=self.INFO_JSON_FILE_NAME)

        self.zip.close()

        return self.get_zip_file_path()


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

        # TODO : remove  'resource' in info_json when all lab are v0.5.0
        if 'resource' in info_json and info_json.get('resource') is None:
            raise Exception(
                f"The resource in {info_json_path} is missing")

        # TODO : remove  'children_resources' in info_json when all lab are v0.5.0
        if 'children_resources' in info_json and not isinstance(info_json.get('children_resources'), list):
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
       # TODO : deprecated, remove when all lab are v0.5.0
        if 'resources' in self.info_json:
            return self.info_json['resources'][0]

        return self.info_json['resource']

    def get_children_resources(self) -> List[ZipResource]:
        # TODO : deprecated, remove when all lab are v0.5.0
        if 'resources' in self.info_json:
            return self.info_json['resources'][1:]

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

# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from json import dump, load
from typing import Dict, List, Optional, Type, TypedDict
from zipfile import ZipFile

from gws_core.brick.brick_helper import BrickHelper
from gws_core.core.decorator.transaction import transaction
from gws_core.core.utils.settings import Settings
from gws_core.core.utils.zip import Zipv2
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.file.fs_node import FSNode
from gws_core.impl.file.fs_node_model import FSNodeModel
from gws_core.model.typing import TypingNameObj
from gws_core.model.typing_manager import TypingManager
from gws_core.resource.kv_store import KVStore
from gws_core.resource.resource import Resource
from gws_core.resource.resource_list_base import ResourceListBase
from gws_core.resource.resource_set import ResourceSet
from gws_core.user.user import User

from .resource_model import ResourceModel, ResourceOrigin
from .resource_service import ResourceService


class ZipOriginInfo(TypedDict):
    lab_id: str
    lab_name: str

    user_id: str
    user_firstname: str
    user_lastname: str

    space_id: str
    space_name: str


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
    zip_version: int
    resources: List[ZipResource]
    origin: ZipOriginInfo


class ResourceZipper():

    ZIP_FILE_NAME = 'resource.zip'
    KV_STORE_FILE_NAME = 'kvstore'
    FS_NODE_FILE_NAME = 'filestore'
    INFO_JSON_FILE_NAME = 'info.json'

    temp_dir: str

    zip: Zipv2

    resource_info: ZipResourceInfo

    shared_by: User

    def __init__(self, shared_by: User):
        self.shared_by = shared_by
        self.temp_dir = Settings.get_instance().make_temp_dir()
        self.zip = Zipv2(self.get_zip_file_path())
        self.resource_info = {
            'zip_version': 1,
            'resources': [],
            'origin': self.generate_origin()
        }

    def generate_origin(self) -> ZipOriginInfo:
        settings = Settings.get_instance()
        space = settings.get_space()
        return {
            'lab_id': None,  # TODO settings.get_lab_id(),
            'lab_name': settings.get_lab_name(),
            'user_id': self.shared_by.id,
            'user_firstname': self.shared_by.first_name,
            'user_lastname': self.shared_by.last_name,
            'space_id': space['id'] if space is not None else None,
            'space_name': space['name'] if space is not None else None
        }

    def add_resource(self, resource_id: str, parent_resource_id: str = None) -> None:

        resource_model: ResourceModel = ResourceService.get_resource_by_id(resource_id)

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

            self.zip.add_fs_node(fs_node_model.path, fs_node_name=fs_node_file_name)
            resource_zip['fs_node_name'] = fs_node_file_name

        self.resource_info['resources'].append(resource_zip)

        # if the resource is a ResourceListBase, add all the children to the zip recursively
        resource: Resource = resource_model.get_resource()
        if isinstance(resource, ResourceListBase) and not isinstance(resource, ResourceSet):
            raise Exception('Only ResourceSet is supported other sub class of ResourceListBase are not supported yet.')

        if isinstance(resource, ResourceSet):
            for child_resource in resource.get_resources_as_set():
                self.add_resource(child_resource._model_id, resource_id)

    def _get_next_resource_index(self) -> int:
        return len(self.resource_info['resources'])

    def get_zip_file_path(self):
        return os.path.join(self.temp_dir, self.ZIP_FILE_NAME)

    def close_zip(self):
        # add the info.json file
        info_json = os.path.join(self.temp_dir, self.INFO_JSON_FILE_NAME)
        with open(info_json, 'w', encoding='UTF-8') as file:
            dump(self.resource_info, file)

        self.zip.add_file(info_json, file_name=self.INFO_JSON_FILE_NAME)

        self.zip.close()


class ResourceUnzipper():

    info_json: ZipResourceInfo

    zip_file_path: str
    temp_dir: str

    resource_models: List[ResourceModel]

    resource_new_id_dict: Dict[str, str]

    def __init__(self, zip_file_path: str) -> None:
        self.info_json = None
        self.zip_file_path = zip_file_path
        self.temp_dir = Settings.get_instance().make_temp_dir()
        self.resource_models = []
        self.resource_new_id_dict = {}
        self._unzip()

    def _unzip(self) -> None:
        with ZipFile(self.zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(self.temp_dir)

    def load_resources(self) -> List[ResourceModel]:

        self._load_info_json()

        self._check_compatibility()

        for zip_resource in self.info_json['resources']:
            resource_model = self._load_resource(zip_resource)

            # store the new id of the resource link to the old id
            self.resource_new_id_dict[zip_resource['id']] = resource_model.id
            self.resource_models.append(resource_model)

        # update the ids stored in the ResourceSet
        self._replace_resource_ids_in_resources()

        return self.resource_models

    def _check_compatibility(self) -> None:
        if self.info_json['zip_version'] != 1:
            raise Exception(f'Zip version {self.info_json["zip_version"]} is not supported.')

        for zip_resource in self.info_json['resources']:
            typing = TypingNameObj.from_typing_name(zip_resource['resource_typing_name'])

            if not BrickHelper.brick_is_loaded(typing.brick_name):
                raise Exception(f'Brick {typing.brick_name} is not loaded.')

            # check that the type exist
            TypingManager.get_typing_from_name_and_check(zip_resource['resource_typing_name'])

    def _load_resource(self, zip_resource: ZipResource) -> ResourceModel:
        resource_model: ResourceModel = ResourceModel()
        resource_model.set_resource_typing_name(zip_resource['resource_typing_name'])
        resource_model.origin = ResourceOrigin.IMPORTED_FROM_LAB
        resource_model.name = zip_resource['name']
        resource_model.data = zip_resource['data']
        resource_model.flagged = True  # flag the resource

        # handle the parent
        if zip_resource['parent_resource_id'] is not None:
            if not zip_resource['parent_resource_id'] in self.resource_new_id_dict:
                raise Exception(f'Parent resource {zip_resource["parent_resource_id"]} not found in info.json')

            # set parent id in this lab
            resource_model.parent_resource_id = self.resource_new_id_dict[zip_resource['parent_resource_id']]

        # create the kvstore
        kv_store: KVStore = None
        if zip_resource.get('kvstore_dir_name') is not None:
            kvstore_path = os.path.join(self.temp_dir, zip_resource['kvstore_dir_name'])

            dest_folder = os.path.join(KVStore.get_base_dir(), resource_model.id)

            FileHelper.move_file_or_dir(kvstore_path, dest_folder)

            kv_store = KVStore.from_filename(resource_model.id)

            resource_model.kv_store_path = kv_store.get_full_path_without_extension()

        # create the fs_node
        if zip_resource.get('fs_node_name') is not None:
            resource_type: Type[FSNode] = TypingManager.get_type_from_name(resource_model.resource_typing_name)

            if not issubclass(resource_type, FSNode):
                raise Exception('Resource type is not a FSNode')

            fsnode_path = os.path.join(self.temp_dir, zip_resource['fs_node_name'])
            node = FSNode(path=fsnode_path)

            resource_model.init_fs_node_model(node, resource_model.name)

        return resource_model

    @transaction()
    def save_all_resources(self) -> List[ResourceModel]:
        for resource_model in self.resource_models:
            resource_model.save_full()

        return self.resource_models

    def _load_info_json(self) -> ZipResourceInfo:
        info_json_path = os.path.join(self.temp_dir, ResourceZipper.INFO_JSON_FILE_NAME)

        if not FileHelper.exists_on_os(info_json_path):
            raise Exception(f'File {info_json_path} not found in the zip file.')

        info_json: ZipResourceInfo = None
        with open(info_json_path, 'r', encoding='UTF-8') as file:
            info_json = load(file)

        if info_json is None:
            raise Exception(f'File {info_json_path} is empty.')

        if not isinstance(info_json.get('zip_version'), int):
            raise Exception(
                f"The zip_version value '{info_json.get('zip_version')}' in {info_json_path} file is invalid, must be an int")

        if not isinstance(info_json.get('resources'), list):
            raise Exception(
                f"The resources value in {info_json_path} file is invalid, must be a list")

        self.info_json = info_json

    def _replace_resource_ids_in_resources(self):
        for resource_model in self.resource_models:

            resource: Resource = resource_model.get_resource()
            result = resource.replace_resource_model_ids(self.resource_new_id_dict)

            if result:
                resource_model.receive_fields_from_resource(resource)

    def get_origin_info(self) -> ZipOriginInfo:
        return self.info_json['origin']

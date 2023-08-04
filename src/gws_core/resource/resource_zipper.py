# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from json import dump
from typing import List, Optional

from typing_extensions import TypedDict

from gws_core.core.service.external_lab_service import (
    ExternalLabService, ExternalLabWithUserInfo)
from gws_core.core.utils.compress.zip import Zip
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.file.fs_node_model import FSNodeModel
from gws_core.resource.kv_store import KVStore
from gws_core.resource.resource import Resource
from gws_core.resource.resource_set.resource_list_base import ResourceListBase
from gws_core.resource.resource_set.resource_set import ResourceSet
from gws_core.user.user import User

from .resource_model import ResourceModel


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

        resource_model: ResourceModel = ResourceModel.get_by_id_and_check(resource_id)

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

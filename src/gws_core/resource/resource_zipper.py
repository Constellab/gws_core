import os
from json import dump

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.utils.compress.zip_compress import ZipCompress
from gws_core.core.utils.settings import Settings
from gws_core.external_lab.external_lab_api_service import ExternalLabApiService
from gws_core.external_lab.external_lab_dto import ExternalLabWithUserInfo
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.file.fs_node_model import FSNodeModel
from gws_core.resource.kv_store import KVStore
from gws_core.resource.resource import Resource
from gws_core.resource.resource_dto import ResourceModelExportDTO
from gws_core.resource.resource_set.resource_list_base import ResourceListBase
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.tag_dto import TagDTO
from gws_core.tag.tag_entity_type import TagEntityType
from gws_core.user.user import User

from .resource_model import ResourceModel


class ResourceExportDTO(BaseModelDTO):
    resource_model_export: ResourceModelExportDTO
    data: dict
    tags: list[TagDTO]

    # True if the resource has a kvstore
    has_kvstore: bool = False

    def get_fs_node_name(self) -> str | None:
        if not self.resource_model_export.fs_node:
            return None
        return (
            f"filestore_{self.resource_model_export.id}_{self.resource_model_export.fs_node.name}"
        )

    def get_kvstore_dir_name(self) -> str:
        return f"kvstore_{self.resource_model_export.id}"


class ResourceExportPackage(BaseModelDTO):
    """Content of the info.json file in the zip file when a resource is zipped"""

    zip_version: int
    resource: ResourceExportDTO | None
    children_resources: list[ResourceExportDTO]
    origin: ExternalLabWithUserInfo


class ResourceZipper:
    """Class to generate a zip file containing everythinga needed to recreate a resource"""

    ZIP_FILE_NAME = "resource.zip"
    INFO_JSON_FILE_NAME = "info.json"
    COMPRESS_EXTENSION = "zip"

    temp_dir: str

    zip: ZipCompress

    resource_info: ResourceExportPackage

    shared_by: User

    EXPORT_VERSION = 2

    def __init__(self, shared_by: User):
        self.shared_by = shared_by
        self.temp_dir = Settings.get_instance().make_temp_dir()
        self.zip = ZipCompress(self.get_zip_file_path())
        self.resource_info = ResourceExportPackage(
            zip_version=self.EXPORT_VERSION,
            resource=None,
            children_resources=[],
            origin=ExternalLabApiService.get_current_lab_info(self.shared_by),
        )

    def add_resource(self, resource: Resource) -> None:
        if not resource.get_model_id():
            raise Exception("Resource must have a model id")
        self.add_resource_model(resource.get_model_id())

    def add_resource_model(self, resource_id: str, parent_resource_id: str | None = None) -> None:
        resource_model: ResourceModel = ResourceModel.get_by_id_and_check(resource_id)

        resource_tags = EntityTagList.find_by_entity(TagEntityType.RESOURCE, resource_id)
        tags_dict = [tag.to_simple_tag().to_dto() for tag in resource_tags.get_tags()]

        resource_model_export = resource_model.to_export_dto()
        resource_model_export.parent_resource_id = parent_resource_id

        resource_zip = ResourceExportDTO(
            resource_model_export=resource_model_export,
            data=resource_model.data,
            tags=tags_dict,
        )

        # add the kvstore
        kvstore: KVStore = resource_model.get_kv_store()
        if kvstore is not None:
            # add the kvstore folder in the zip and name this folder kvstore
            self.zip.add_dir(kvstore.full_file_dir, dir_name=resource_zip.get_kvstore_dir_name())
            resource_zip.has_kvstore = True

        # add the fs_node
        fs_node_model: FSNodeModel = resource_model.fs_node_model
        if fs_node_model is not None:
            self.zip.add_fs_node(fs_node_model.path, fs_node_name=resource_zip.get_fs_node_name())

        # add the resource info
        if parent_resource_id is None:
            self.resource_info.resource = resource_zip
        else:
            self.resource_info.children_resources.append(resource_zip)

        # if the resource is a ResourceListBase, add all the children to the zip recursively
        resource: Resource = resource_model.get_resource()
        if isinstance(resource, ResourceListBase):
            for child_id in resource.get_resource_model_ids():
                self.add_resource_model(child_id, resource_id)

    def get_zip_file_path(self):
        return os.path.join(self.temp_dir, self.ZIP_FILE_NAME)

    def close_zip(self) -> str:
        # add the info.json file
        info_json = os.path.join(self.temp_dir, self.INFO_JSON_FILE_NAME)
        with open(info_json, "w", encoding="UTF-8") as file:
            dump(self.resource_info.to_json_dict(), file)

        self.zip.add_file(info_json, file_name=self.INFO_JSON_FILE_NAME)

        self.zip.close()

        return self.get_zip_file_path()

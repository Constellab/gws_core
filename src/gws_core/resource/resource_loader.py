import os
from json import load

from gws_core.core.utils.compress.compress import Compress
from gws_core.core.utils.settings import Settings
from gws_core.external_lab.external_lab_dto import ExternalLabWithUserInfo
from gws_core.impl.file.file import File
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.file.folder import Folder
from gws_core.impl.file.fs_node import FSNode
from gws_core.model.typing_manager import TypingManager
from gws_core.resource.kv_store import KVStore
from gws_core.resource.r_field.primitive_r_field import UUIDRField
from gws_core.resource.resource import Resource
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_factory import ResourceFactory
from gws_core.resource.resource_set.resource_list_base import ResourceListBase
from gws_core.share.shared_dto import ShareEntityCreateMode
from gws_core.tag.tag_helper import TagHelper

from .resource_zipper import ResourceExportDTO, ResourceExportPackage, ResourceZipper


class ResourceLoader:
    """Class to load a resource from a folder"""

    info_json: ResourceExportPackage | None

    _resource_folder_path: str

    _resource: Resource | None = None
    # dict where key is old resource model id and value is the resource
    _children_resources: dict[str, Resource]

    mode: ShareEntityCreateMode
    resource_origin: ResourceOrigin | None

    skip_tags: bool

    def __init__(
        self,
        resource_folder_path: str,
        mode: ShareEntityCreateMode,
        resource_origin: ResourceOrigin | None = None,
        skip_tags: bool = False,
    ) -> None:
        self.info_json = None
        self._resource_folder_path = resource_folder_path
        self._children_resources = {}
        self.mode = mode
        self.resource_origin = resource_origin
        self.skip_tags = skip_tags

    def is_resource_zip(self) -> bool:
        """Return true if the zip file is a resource zip file"""
        try:
            self._load_info_json()
            return True
        except Exception:
            return False

    def load_resource(self) -> Resource:
        if self._resource is not None:
            return self._resource

        if not self.is_resource_zip():
            return self.load_fs_node_resource()

        self._check_compatibility()

        main_resource = self.get_main_resource()
        self._resource = self._load_resource(main_resource)

        if isinstance(self._resource, ResourceListBase):
            # load all the children resources
            for zip_resource in self.get_children_zip_resources():
                resource: Resource = self._load_resource(zip_resource)
                self._children_resources[zip_resource.resource_model_export.id] = resource

            # replace the resources in the ResourceListBase by the new ones
            self._resource.replace_resources_by_model_id(self._children_resources)

        return self._resource

    def _check_compatibility(self) -> None:
        if self._load_info_json().zip_version != ResourceZipper.EXPORT_VERSION:
            raise Exception(f"Zip version {self._load_info_json().zip_version} is not supported.")

        for zip_resource in self.get_all_zip_resources():
            TypingManager.check_typing_name_compatibility(
                zip_resource.resource_model_export.resource_typing_name
            )

    def _load_resource(self, zip_resource: ResourceExportDTO) -> Resource:
        resource_export = zip_resource.resource_model_export

        # create the kvstore
        kv_store: KVStore | None = None
        if zip_resource.has_kvstore:
            kvstore_path = os.path.join(
                self._resource_folder_path, zip_resource.get_kvstore_dir_name(), KVStore.FILE_NAME
            )

            kv_store = KVStore(kvstore_path)

        resource_type: type[Resource] = TypingManager.get_and_check_type_from_name(
            resource_export.resource_typing_name
        )

        tags = []
        if not self.skip_tags:
            tags_dict = zip_resource.tags or []
            tags = TagHelper.tags_dto_to_list(tags_dict)

            # Set the external lab origin for all tags
            for tag in tags:
                tag.set_external_lab_origin(self.get_origin_info().lab.id)

        resource_model_id: str | None = None
        if self.mode == ShareEntityCreateMode.KEEP_ID:
            resource_model_id = resource_export.id

        resource = ResourceFactory.create_resource(
            resource_type,
            kv_store=kv_store,
            data=zip_resource.data,
            name=resource_export.name,
            tags=tags,
            resource_model_id=resource_model_id,
            style=resource_export.style,
        )

        if self.mode == ShareEntityCreateMode.NEW_ID:
            # generate a new uid for the resource
            resource.uid = UUIDRField().get_default_value()

        # if the resource is an fs_node
        if zip_resource.resource_model_export.fs_node:
            if not isinstance(resource, FSNode):
                raise Exception("Resource type is not a FSNode")

            fs_node_name = zip_resource.get_fs_node_name()
            # set the path of the resource node
            resource.path = os.path.join(self._resource_folder_path, fs_node_name)
            # clear other values
            resource.file_store_id = None
            resource.is_symbolic_link = False

        if self.resource_origin is not None:
            resource.__set_origin__(self.resource_origin)

        return resource

    def _load_info_json(self) -> ResourceExportPackage:
        if self.info_json is not None:
            return self.info_json

        info_json_path = os.path.join(
            self._resource_folder_path, ResourceZipper.INFO_JSON_FILE_NAME
        )

        if not FileHelper.exists_on_os(info_json_path):
            raise Exception(f"File {info_json_path} not found in the zip file.")

        info_json: dict
        with open(info_json_path, encoding="UTF-8") as file:
            info_json = load(file)

        if info_json is None:
            raise Exception(f"File {info_json_path} is empty.")

        if not isinstance(info_json.get("zip_version"), int):
            raise Exception(
                f"The zip_version value '{info_json.get('zip_version')}' in {info_json_path} file is invalid, must be an int"
            )

        if info_json.get("resource") is None:
            raise Exception(f"The resource in {info_json_path} is missing")

        if not isinstance(info_json.get("children_resources"), list):
            raise Exception(
                f"The children_resources value in {info_json_path} file is invalid, must be a list"
            )

        self.info_json = ResourceExportPackage.from_json(info_json)

        return self.info_json

    def load_fs_node_resource(self) -> FSNode:
        """Load the File or Folder resource from folder if the folder
        is not a resource export but only files.
        If there is 1 file or folder in the folder, return it.
        If there is more than 1 file in the folder, return the folder.
        """
        # count the files and folders directly in the result folder
        count = len(os.listdir(self._resource_folder_path))

        if count == 0:
            raise Exception("The zipped file does not contains any resource.")

        if count == 1:
            node_name = os.listdir(self._resource_folder_path)[0]
            sub_path = os.path.join(self._resource_folder_path, node_name)
            if os.path.isdir(sub_path):
                return Folder(sub_path)
            else:
                return File(sub_path)
        else:
            # if there is more than 1 file or folder, return a Folder
            return Folder(self._resource_folder_path)

    def get_origin_info(self) -> ExternalLabWithUserInfo:
        return self._load_info_json().origin

    def get_main_resource_origin_id(self) -> str:
        return self._load_info_json().resource.resource_model_export.id

    def get_main_resource(self) -> ResourceExportDTO:
        return self._load_info_json().resource

    def get_children_zip_resources(self) -> list[ResourceExportDTO]:
        """Return the children zip resource DTOs from the export package."""
        return self._load_info_json().children_resources

    def get_all_zip_resources(self) -> list[ResourceExportDTO]:
        """Return all zip resource DTOs (main + children) from the export package."""
        return [self.get_main_resource()] + self.get_children_zip_resources()

    def get_all_generated_resources(self) -> list[Resource]:
        resource = self.load_resource()
        return [resource] + list(self._children_resources.values())

    def get_children_dto(self, children_id: str) -> ResourceExportDTO | None:
        """Return the child resource DTO with the given id, or None if not found."""
        for child in self.get_children_zip_resources():
            if child.resource_model_export.id == children_id:
                return child
        return None

    def get_generated_children_resources(self) -> dict[str, Resource]:
        return self._children_resources

    def delete_resource_folder(self) -> None:
        FileHelper.delete_dir(self._resource_folder_path)

    @classmethod
    def from_compress_file(
        cls,
        compress_file_path: str,
        mode: ShareEntityCreateMode,
        resource_origin: ResourceOrigin | None = None,
        skip_tags: bool = False,
    ) -> "ResourceLoader":
        """Uncompress a file and create a ResourceLoader"""
        temp_dir = Settings.get_instance().make_temp_dir()
        Compress.smart_decompress(compress_file_path, temp_dir)
        return ResourceLoader(temp_dir, mode, resource_origin, skip_tags)

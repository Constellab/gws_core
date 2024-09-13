

from os import path
from typing import Any, ByteString, Dict, List, Optional

from fastapi.responses import FileResponse
from mypy_boto3_s3.type_defs import (ListObjectsV2OutputTypeDef, ObjectTypeDef,
                                     TagTypeDef)

from gws_core.core.decorator.transaction import transaction
from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.entity_navigator.entity_navigator_service import \
    EntityNavigatorService
from gws_core.entity_navigator.entity_navigator_type import EntityType
from gws_core.folder.space_folder import SpaceFolder
from gws_core.folder.space_folder_service import SpaceFolderService
from gws_core.impl.file.file import File
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.s3.s3_server_context import S3ServerContext
from gws_core.impl.s3.s3_server_exception import (S3ServerException,
                                                  S3ServerNoSuchKey)
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.resource_model_search_builder import \
    ResourceModelSearchBuilder
from gws_core.resource.resource_service import ResourceService
from gws_core.tag.entity_tag import EntityTag
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.tag import Tag, TagOrigins
from gws_core.tag.tag_dto import TagOriginType


class S3ServerService:
    """Class to manage file upload to this lab as an S3 server
    """

    # defaumlt bucket name for folders storage
    FOLDERS_BUCKET_NAME = 'data-hub-storage'

    # Mandatory and not updatable tags for the S3 server object
    STORAGE_TAG_NAME = 'storage'
    BUCKET_TAG_NAME = 'bucket'
    KEY_TAG_NAME = 'key'

    # Optional tags pass in the upload request to set data on the object (not saved as tag)
    FOLDER_TAG_NAME = 'folder'
    NAME_TAG_NAME = 'name'

    @classmethod
    def create_bucket(cls, bucket_name: str) -> None:
        if not cls._is_folder_doc_bucket(bucket_name):
            raise S3ServerException(status_code=400, code='invalid_bucket_name',
                                    message='Invalid bucket name, only folder storage is allowed for now',
                                    bucket_name=bucket_name)

    @classmethod
    def list_objects(cls, bucket_name: str,
                     prefix: str = None, max_keys: int = 1000) -> ListObjectsV2OutputTypeDef:
        """List objects in a bucket
        """

        with S3ServerContext(bucket_name):
            search_builder = cls._get_s3_expression_builder(bucket_name, prefix=prefix)
            search_builder.add_ordering(ResourceModel.name)

            resources = search_builder.build_search()

            bucket_objects = [cls._resource_to_s3_object(resource) for resource in resources]

            return {
                'Name': bucket_name,
                'Prefix': prefix,
                'Marker': '',
                'MaxKeys': max_keys,
                'IsTruncated': False,
                'Contents': bucket_objects,
            }

    @classmethod
    @transaction()
    def upload_object(cls, bucket_name: str,
                      key: str, data: ByteString,
                      tags: Dict[str, str] = None) -> None:
        """Upload an object to the bucket
        """

        # check if it already exists
        resource_model = cls._get_object(bucket_name, key)

        if resource_model:
            cls._update_object(bucket_name, key, data, resource_model, tags)
        else:
            cls._create_object(bucket_name, key, data, tags)

    @classmethod
    def _create_object(cls, bucket_name: str,
                       key: str, data: ByteString,
                       tags: Dict[str, str] = None) -> None:
        with S3ServerContext(bucket_name, key):

            folder: SpaceFolder = None
            if cls._is_folder_doc_bucket(bucket_name):
                folder = cls._get_and_check_folder_bucket(bucket_name, tags.get(cls.FOLDER_TAG_NAME))
            else:
                # for now we allow only folder documents to be uploaded
                raise S3ServerException(status_code=400, code='invalid_bucket_name',
                                        message='Invalid bucket name, only folder storage is allowed for now',
                                        bucket_name=bucket_name, key=key)

            # create a file in a temp folder
            temp_folder = Settings.make_temp_dir()

            filename = FileHelper.get_name_with_extension(key)
            file_path = path.join(temp_folder, filename)
            with open(file_path, 'wb') as write_file:
                write_file.write(data)

            # make a resource from the file
            file = File(file_path)

            resource_origin = ResourceOrigin.S3_FOLDER_STORAGE if cls._is_folder_doc_bucket(
                bucket_name) else ResourceOrigin.UPLOADED

            resource_model = ResourceModel.from_resource(file, resource_origin)
            if tags.get(cls.NAME_TAG_NAME):
                resource_model.name = tags[cls.NAME_TAG_NAME]
            else:
                resource_model.name = FileHelper.get_name_with_extension(key)
            resource_model.folder = folder

            resource_model = resource_model.save_full()

            resource_tags = EntityTagList.find_by_entity(EntityType.RESOURCE, resource_model.id)

            # Add the tags, make sure they are not propagable
            origins = cls.get_tag_origin()
            resource_tags.add_tag(Tag(cls.STORAGE_TAG_NAME, 's3', is_propagable=False, origins=origins))
            resource_tags.add_tag(Tag(cls.BUCKET_TAG_NAME, bucket_name, is_propagable=False, origins=origins))
            resource_tags.add_tag(Tag(cls.KEY_TAG_NAME, key, is_propagable=False, origins=origins))

            # add the additional tags
            if tags:
                cleaned_tags = cls.get_additional_tags(tags)
                for key, value in cleaned_tags.items():
                    resource_tags.add_tag(Tag(key, value, is_propagable=False, origins=origins))

    @classmethod
    def _update_object(cls, bucket_name: str,
                       key: str, data: ByteString,
                       resource_model: ResourceModel,
                       tags: Dict[str, str] = None) -> None:
        with S3ServerContext(bucket_name, key):

            if not resource_model.fs_node_model:
                raise S3ServerException(status_code=500, code='invalid_object',
                                        message='Object is not a file', bucket_name=bucket_name, key=key)

            ResourceService.check_if_resource_is_used(resource_model)

            if data:
                # override the file
                file_path = resource_model.fs_node_model.path
                with open(file_path, 'wb') as write_file:
                    write_file.write(data)

                # refresh the size of the file
                resource_model.fs_node_model.size = FileHelper.get_size(file_path)
                resource_model.fs_node_model.save()

            # update the last modified date
            resource_model.last_modified_at = DateHelper.now_utc()

            # update folder if provided
            if tags.get(cls.FOLDER_TAG_NAME):
                resource_model.folder = cls._get_folder_and_check(tags.get(cls.FOLDER_TAG_NAME))

            # update the name if provided
            resource_model.name = tags.get(cls.NAME_TAG_NAME, resource_model.name)
            resource_model.save()

            # update other tags
            cls.update_object_tags(bucket_name, key, tags)

    @classmethod
    def get_object(cls, bucket_name: str, key: str) -> FileResponse:
        """Get an object from the bucket
        """
        resource: ResourceModel = cls._get_object_and_check(bucket_name, key)

        return FileHelper.create_file_response(resource.fs_node_model.path)

    @classmethod
    def delete_object(cls, bucket_name: str, key: str) -> None:
        """Delete an object from the bucket
        """
        resource: ResourceModel = cls._get_and_check_before_delete_object(bucket_name, key)

        with S3ServerContext(bucket_name, key):
            EntityNavigatorService.delete_resource(resource_id=resource.id, allow_s3_folder_storage=True)

    @classmethod
    def delete_objects(cls, bucket_name: str, keys: List[str]) -> None:
        """Delete multiple objects, ignore if the object does not exist

        :param bucket_name: _description_
        :type bucket_name: str
        :param keys: _description_
        :type keys: List[str]
        """

        resources: List[ResourceModel] = []
        for key in keys:

            resource = cls._get_object(bucket_name, key)
            if resource is None:
                Logger.warning(f"Object {key} not found in bucket {bucket_name}, skipping deletion.")
                continue

            resources.append(cls._get_and_check_before_delete_object(bucket_name, key))

        with S3ServerContext(bucket_name):
            for resource in resources:
                EntityNavigatorService.delete_resource(resource_id=resource.id, allow_s3_folder_storage=True)

    @classmethod
    def _get_and_check_before_delete_object(cls, bucket_name: str, key: str) -> ResourceModel:
        resource: ResourceModel = cls._get_object_and_check(bucket_name, key)
        result = EntityNavigatorService.check_impact_delete_resource(resource.id)
        if result.has_entities():
            raise S3ServerException(
                status_code=400, code='delete_impact',
                message='Cannot delete the resource because it is used in an next experiment or a report.',
                bucket_name=bucket_name, key=key)
        return resource

    @classmethod
    def head_object(cls, bucket_name: str, key: str) -> dict:
        """Head an object from the bucket
        """
        resource = cls._get_object_and_check(bucket_name, key)
        return {
            'Content-Length': str(resource.fs_node_model.size),
            'Content-Type': FileHelper.get_mime(resource.fs_node_model.path),
            'Last-Modified': DateHelper.to_rfc7231_str(resource.last_modified_at),
        }

    @classmethod
    def _get_object(cls, bucket_name: str, key: str) -> Optional[ResourceModel]:
        """Get an object from the bucket
        """
        search_builder = cls._get_s3_expression_builder(bucket_name=bucket_name, key=key)
        return search_builder.build_search().first()

    @classmethod
    def _get_object_and_check(cls, bucket_name: str, key: str) -> ResourceModel:
        """Get an object from the bucket
        """
        resource = cls._get_object(bucket_name, key)

        if resource is None:
            raise S3ServerNoSuchKey(bucket_name, key)

        return resource

    @classmethod
    def _is_folder_doc_bucket(cls, bucket_name: str) -> bool:
        """Check if the bucket is the folder document bucket
        """
        return bucket_name == cls.FOLDERS_BUCKET_NAME

    @classmethod
    def _get_and_check_folder_bucket(cls, bucket_name: str, folder_tag: str) -> SpaceFolder:
        """Get a folder bucket
        """
        if not cls._is_folder_doc_bucket(bucket_name):
            raise S3ServerException(status_code=400, code='invalid_bucket_name',
                                    message='Invalid bucket name',
                                    bucket_name=bucket_name)

        if not folder_tag:
            raise S3ServerException(status_code=400, code='invalid_key',
                                    message='Missing folder in the tags',
                                    bucket_name=bucket_name)

        return cls._get_folder_and_check(folder_tag)

    @classmethod
    def _get_folder_and_check(cls, folder_id: str) -> SpaceFolder:
        """Get a folder by id
        """
        folder = SpaceFolder.get_by_id(folder_id)

        if folder is None:
            # if the folder is not found, try to sync it
            try:
                Logger.info(f"Folder {folder_id} not found in lab, trying to sync it")
                SpaceFolderService.synchronize_folder(folder_id)

                # if sync is success to the new folder
                folder = SpaceFolder.get_by_id(folder_id)
            except Exception as e:
                Logger.error(f"Error while synchronizing folder {folder_id}. Error {str(e)}")

        if folder is None:
            raise S3ServerException(status_code=400, code='invalid_folder_id',
                                    message='Folder not found in data hub, try to sync the lab folders',
                                    bucket_name='', key='')

        return folder

    @classmethod
    def _resource_to_s3_object(cls, resource: ResourceModel) -> ObjectTypeDef:
        entity_tag: EntityTag = EntityTag.find_by_tag_key_and_entity('key', EntityType.RESOURCE, resource.id).first()
        if not entity_tag:
            raise S3ServerException(status_code=500, code='invalid_resource',
                                    message='Resource has no key tag', bucket_name='')
        return {
            'Key': entity_tag.tag_value,
            'LastModified': DateHelper.to_iso_str(resource.last_modified_at),
            'ETag': '',
            'Size': resource.fs_node_model.size,
            'Owner': {
                'ID': '',
                'DisplayName': 'lab'
            },
            'StorageClass': 'STANDARD'
        }

    @classmethod
    def _get_s3_expression_builder(cls, bucket_name: str,
                                   key: str = None, prefix: str = None) -> ResourceModelSearchBuilder:
        """Method to get the expression builder to filter resource model by bucket, key...
        """
        search_builder = ResourceModelSearchBuilder()

        search_builder.add_tag_filter(Tag(cls.STORAGE_TAG_NAME, 's3'))
        search_builder.add_tag_filter(Tag(cls.BUCKET_TAG_NAME, bucket_name))

        search_builder.add_expression(ResourceModel.fs_node_model.is_null(False))

        if cls._is_folder_doc_bucket(bucket_name):
            search_builder.add_expression(ResourceModel.origin == ResourceOrigin.S3_FOLDER_STORAGE)
        else:
            search_builder.add_expression(ResourceModel.origin == ResourceOrigin.UPLOADED)

        if key:
            search_builder.add_tag_filter(Tag(cls.KEY_TAG_NAME, key))

        if prefix:
            if not prefix.endswith('/'):
                prefix += '/'
            search_builder.add_tag_filter(Tag(cls.KEY_TAG_NAME, prefix), 'START_WITH')

        return search_builder

    ##################################################### TAGGING #####################################################

    @classmethod
    def get_object_tags(cls, bucket_name: str, key: str) -> Any:
        """Get the tags of an object
        """
        resource = cls._get_object_and_check(bucket_name, key)

        tags = EntityTagList.find_by_entity(EntityType.RESOURCE, resource.id).get_tags()

        s3_tags: List[TagTypeDef] = []
        for tag in tags:
            s3_tags.append({
                'Key': tag.tag_key,
                'Value': tag.tag_value
            })

        if resource.folder:
            s3_tags.append({'Key': cls.FOLDER_TAG_NAME, 'Value': resource.folder.id})
        s3_tags.append({'Key': cls.NAME_TAG_NAME, 'Value': resource.name})

        return {
            "VersionId": "1",
            'TagSet': {"Tag": s3_tags},
            'ResponseMetadata': None
        }

    @classmethod
    def update_object_tags(cls, bucket_name: str, key: str, tags: Dict[str, str]) -> None:
        """Update the tags of an object
        """
        resource = cls._get_object_and_check(bucket_name, key)
        entity_tags = EntityTagList.find_by_entity(EntityType.RESOURCE, resource.id)

        # delete all additional tags
        additional_current_tags = cls.get_additional_tags(entity_tags.get_tags_as_dict())
        for key, value in additional_current_tags.items():
            entity_tags.delete_tag(Tag(key, value))

        # add the new tags
        additional_new_tags = cls.get_additional_tags(tags)
        for key, value in additional_new_tags.items():
            entity_tags.add_tag(Tag(key, value, origins=cls.get_tag_origin()))

    @classmethod
    def get_additional_tags(cls, tags: Dict[str, str]) -> Dict[str, str]:
        """Return the additional tags to save on the object, it removes the predefined tags
        """
        cleaned_tags = {}
        for key, value in tags.items():
            # skip predefined tags
            if key in [cls.STORAGE_TAG_NAME, cls.BUCKET_TAG_NAME, cls.KEY_TAG_NAME,
                       cls.FOLDER_TAG_NAME, cls.NAME_TAG_NAME]:
                continue
            cleaned_tags[key] = value
        return cleaned_tags

    @classmethod
    def get_tag_origin(cls) -> TagOrigins:
        """Get the origin of a tag
        """
        return TagOrigins(TagOriginType.S3, 's3')

    ##################################################### OTHER METHODS #####################################################

    @staticmethod
    def convert_query_param_string_to_dict(query_param: str) -> dict:
        """
        Convert a query parameter string to a dictionary

        :param query_param: the query parameter string
        :return: the dictionary
        """
        if not query_param:
            return {}

        return dict([param.split('=') for param in query_param.split('&')])



from os import path
from typing import ByteString, Dict, List, Optional

from fastapi.responses import FileResponse
from mypy_boto3_s3.type_defs import (ListObjectsV2OutputTypeDef, ObjectTypeDef,
                                     TagTypeDef)

from gws_core.core.classes.search_builder import SearchOperator
from gws_core.core.decorator.transaction import transaction
from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.entity_navigator.entity_navigator_service import \
    EntityNavigatorService
from gws_core.folder.space_folder import SpaceFolder
from gws_core.folder.space_folder_service import SpaceFolderService
from gws_core.impl.file.file import File
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.s3.abstract_s3_service import AbstractS3Service
from gws_core.impl.s3.s3_server_context import S3ServerContext
from gws_core.impl.s3.s3_server_dto import S3GetTagResponse, S3UpdateTagRequest
from gws_core.impl.s3.s3_server_exception import (S3ServerException,
                                                  S3ServerNoSuchKey)
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.resource_search_builder import ResourceSearchBuilder
from gws_core.resource.resource_service import ResourceService
from gws_core.tag.entity_tag import EntityTag
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.tag import Tag, TagOrigins
from gws_core.tag.tag_dto import TagOriginType
from gws_core.tag.tag_entity_type import TagEntityType


class DataHubS3ServerService(AbstractS3Service):
    """Class to manage file upload to this lab as an S3 server for the data hub.
    """

    # default bucket name for folders storage
    FOLDERS_BUCKET_NAME = 'data-hub-storage'

    # Mandatory and not updatable tags for the S3 server object
    STORAGE_TAG_NAME = 'storage'
    STORAGE_TAG_VALUE = 's3'
    BUCKET_TAG_NAME = 'bucket'
    KEY_TAG_NAME = 'key'

    # Optional tags pass in the upload request to set data on the object (not saved as tag)
    FOLDER_TAG_NAME = 'folder'
    NAME_TAG_NAME = 'name'

    def __init__(self, bucket_name: str):
        """Initialize the service with a bucket name"""
        if bucket_name != self.FOLDERS_BUCKET_NAME:
            raise S3ServerException(
                status_code=400, code='invalid_bucket_name',
                message=f"Invalid bucket name, only '{self.FOLDERS_BUCKET_NAME}' is allowed for now",
                bucket_name=bucket_name)
        super().__init__(bucket_name)

    def create_bucket(self) -> None:
        # No need to create the bucket
        pass

    def list_objects(self, prefix: str = None, max_keys: int = 1000, delimiter: str = None,
                     continuation_token: str = None, start_after: str = None) -> ListObjectsV2OutputTypeDef:
        """List objects in a bucket
        """

        with S3ServerContext(self.bucket_name):
            search_builder = self._get_s3_expression_builder(prefix=prefix)
            search_builder.add_ordering(ResourceModel.name)

            resources = search_builder.build_search()

            bucket_objects = [self._resource_to_s3_object(resource) for resource in resources]

            return {
                'Name': self.bucket_name,
                'Prefix': prefix,
                'MaxKeys': max_keys,
                'IsTruncated': False,
                'Contents': bucket_objects,
                'KeyCount': len(bucket_objects),
                'ContinuationToken': '',
                'NextContinuationToken': '',
                'StartAfter': '',
                'Delimiter': '',
                'EncodingType': 'url',
                'RequestCharged': 'requester',
                'ResponseMetadata': {
                    'RequestId': '',
                    'HTTPStatusCode': 200,
                    'HTTPHeaders': {},
                    'RetryAttempts': 0
                },
            }

    @transaction()
    def upload_object(self, key: str, data: ByteString, tags: Dict[str, str] = None,
                      last_modified: float = None) -> None:
        """Upload an object to the bucket
        """

        # check if it already exists
        resource_model = self._get_object(key)

        if resource_model:
            self._update_object(key, data, resource_model, tags)
        else:
            self._create_object(key, data, tags)

    def _create_object(self, key: str, data: ByteString, tags: Dict[str, str] = None) -> None:
        with S3ServerContext(self.bucket_name, key):

            self._get_and_check_folder_bucket(tags.get(self.FOLDER_TAG_NAME) if tags else None)

            # create a file in a temp folder
            temp_folder = Settings.make_temp_dir()

            filename = FileHelper.get_name_with_extension(key)
            file_path = path.join(temp_folder, filename)
            with open(file_path, 'wb') as write_file:
                write_file.write(data)

            # make a resource from the file
            file = File(file_path)

            resource_model = ResourceModel.from_resource(file, ResourceOrigin.S3_FOLDER_STORAGE)
            self._update_resource_from_tags(resource_model, tags)

            # set default name of resource if not set in tags
            if not resource_model.name:
                resource_model.name = FileHelper.get_name_with_extension(key)

            resource_model = resource_model.save_full()

            resource_tags = EntityTagList.find_by_entity(TagEntityType.RESOURCE, resource_model.id)

            # Add the tags, make sure they are not propagable
            origins = self.get_tag_origin()
            resource_tags.add_tag(Tag(self.STORAGE_TAG_NAME, self.STORAGE_TAG_VALUE, is_propagable=False,
                                  origins=origins, auto_parse=True))
            resource_tags.add_tag(Tag(self.BUCKET_TAG_NAME, self.bucket_name,
                                  is_propagable=False, origins=origins, auto_parse=True))
            resource_tags.add_tag(Tag(self.KEY_TAG_NAME, key, is_propagable=False, origins=origins, auto_parse=True))

            # add the additional tags
            if tags:
                cleaned_tags = self.get_additional_tags(tags)
                for tag_key, tag_value in cleaned_tags.items():
                    resource_tags.add_tag(Tag(tag_key, tag_value, is_propagable=False,
                                          origins=origins, auto_parse=True))

    def _update_object(self, key: str, data: ByteString,
                       resource_model: ResourceModel,
                       tags: Dict[str, str] = None) -> None:
        with S3ServerContext(self.bucket_name, key):

            if not resource_model.fs_node_model:
                raise S3ServerException(status_code=500, code='invalid_object',
                                        message='Object is not a file', bucket_name=self.bucket_name, key=key)

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

            resource_model = self._update_resource_from_tags(resource_model, tags)

            resource_model.save()

            # update other tags
            self.update_object_tags_dict(key, tags)

    def get_object(self, key: str) -> FileResponse:
        """Get an object from the bucket
        """
        resource: ResourceModel = self._get_object_and_check(key)

        return FileHelper.create_file_response(resource.fs_node_model.path)

    def delete_object(self, key: str) -> None:
        """Delete an object from the bucket
        """
        resource: ResourceModel = self._get_and_check_before_delete_object(key)

        with S3ServerContext(self.bucket_name, key):
            EntityNavigatorService.delete_resource(resource_id=resource.id, allow_s3_folder_storage=True)

    def delete_objects(self, keys: List[str]) -> None:
        """Delete multiple objects, ignore if the object does not exist

        :param keys: _description_
        :type keys: List[str]
        """

        resources: List[ResourceModel] = []
        for key in keys:

            resource = self._get_object(key)
            if resource is None:
                Logger.warning(f"Object {key} not found in bucket {self.bucket_name}, skipping deletion.")
                continue

            resources.append(self._get_and_check_before_delete_object(key))

        with S3ServerContext(self.bucket_name):
            for resource in resources:
                EntityNavigatorService.delete_resource(resource_id=resource.id, allow_s3_folder_storage=True)

    def _get_and_check_before_delete_object(self, key: str) -> ResourceModel:
        resource: ResourceModel = self._get_object_and_check(key)
        result = EntityNavigatorService.check_impact_delete_resource(resource.id)
        if result.has_entities():
            raise S3ServerException(
                status_code=400, code='delete_impact',
                message='Cannot delete the resource because it is used in an next scenario or a note.',
                bucket_name=self.bucket_name, key=key)
        return resource

    def head_object(self, key: str) -> dict:
        """Head an object from the bucket
        """
        resource = self._get_object_and_check(key)
        return {
            'Content-Length': str(resource.fs_node_model.size),
            'Content-Type': FileHelper.get_mime(resource.fs_node_model.path),
            'Last-Modified': DateHelper.to_rfc7231_str(resource.last_modified_at),
        }

    def _get_object(self, key: str) -> Optional[ResourceModel]:
        """Get an object from the bucket
        """
        search_builder = self._get_s3_expression_builder(key=key)
        return search_builder.build_search().first()

    def _get_object_and_check(self, key: str) -> ResourceModel:
        """Get an object from the bucket
        """
        resource = self._get_object(key)

        if resource is None:
            raise S3ServerNoSuchKey(self.bucket_name, key)

        return resource

    def _get_and_check_folder_bucket(self, folder_tag: str) -> SpaceFolder:
        """Get a folder bucket
        """

        if not folder_tag:
            raise S3ServerException(status_code=400, code='invalid_key',
                                    message='Missing folder in the tags',
                                    bucket_name=self.bucket_name)

        return self._get_folder_and_check(folder_tag)

    def _get_folder_and_check(self, folder_id: str) -> SpaceFolder:
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

    def _resource_to_s3_object(self, resource: ResourceModel) -> ObjectTypeDef:
        entity_tag: EntityTag = EntityTag.find_by_tag_key_and_entity('key', TagEntityType.RESOURCE, resource.id).first()
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

    def _get_s3_expression_builder(self, key: str = None, prefix: str = None) -> ResourceSearchBuilder:
        """Method to get the expression builder to filter resource model by bucket, key...
        """
        search_builder = ResourceSearchBuilder()

        search_builder.add_tag_filter(Tag(self.STORAGE_TAG_NAME, self.STORAGE_TAG_VALUE, auto_parse=True))
        search_builder.add_tag_filter(Tag(self.BUCKET_TAG_NAME, self.bucket_name, auto_parse=True))

        search_builder.add_expression(ResourceModel.fs_node_model.is_null(False))

        search_builder.add_expression(ResourceModel.origin == ResourceOrigin.S3_FOLDER_STORAGE)

        if key:
            search_builder.add_tag_filter(Tag(self.KEY_TAG_NAME, key, auto_parse=True))

        if prefix:
            if not prefix.endswith('/'):
                prefix += '/'
            search_builder.add_tag_filter(Tag(self.KEY_TAG_NAME, prefix, auto_parse=True), SearchOperator.START_WITH)

        return search_builder

    ##################################################### TAGGING #####################################################

    def get_object_tags(self, key: str) -> S3GetTagResponse:
        """Get the tags of an object
        """
        resource = self._get_object_and_check(key)

        tags = EntityTagList.find_by_entity(TagEntityType.RESOURCE, resource.id).get_tags()

        s3_tags: List[TagTypeDef] = []
        for tag in tags:
            s3_tags.append({
                'Key': tag.tag_key,
                'Value': tag.tag_value
            })

        if resource.folder:
            s3_tags.append({'Key': self.FOLDER_TAG_NAME, 'Value': resource.folder.id})
        s3_tags.append({'Key': self.NAME_TAG_NAME, 'Value': resource.name})

        return {
            "VersionId": "1",
            'TagSet': {"Tag": s3_tags},
            'ResponseMetadata': None
        }

    def update_object_tags(self, key: str, tags: S3UpdateTagRequest) -> None:
        """Update the tags of an object
        """
        if not tags.get('TagSet') or 'Tag' not in tags['TagSet']:
            raise S3ServerException(status_code=400, code='invalid_tags',
                                    message='Invalid tags', bucket_name=self.bucket_name, key=key)

        tags_list = tags['TagSet']['Tag']
        # when there is only 1 tag, it is not a list
        if not isinstance(tags_list, list):
            tags_list = [tags_list]

        tags_dict = {}
        for tag in tags_list:
            tags_dict[tag['Key']] = tag['Value']

        with S3ServerContext(self.bucket_name, key):
            self.update_object_tags_dict(key, tags_dict)

    def update_object_tags_dict(self, key: str, tags: Dict[str, str]) -> None:
        """Update the tags of an object
        """
        resource = self._get_object_and_check(key)
        entity_tags = EntityTagList.find_by_entity(TagEntityType.RESOURCE, resource.id)

        # delete all additional tags
        additional_current_tags = self.get_additional_tags(entity_tags.get_tags_as_dict())
        for tag_key, tag_value in additional_current_tags.items():
            entity_tags.delete_tag(Tag(tag_key, tag_value, auto_parse=True))

        # add the new tags
        additional_new_tags = self.get_additional_tags(tags)
        for tag_key, tag_value in additional_new_tags.items():
            entity_tags.add_tag(Tag(tag_key, tag_value, origins=self.get_tag_origin(), auto_parse=True))

        resource = self._update_resource_from_tags(resource, tags)
        resource.save()

    def _update_resource_from_tags(self, resource: ResourceModel, tags: Dict[str, str]) -> ResourceModel:
        """Update a resource from the tags
        """
        if tags and tags.get(self.FOLDER_TAG_NAME):
            folder = self._get_folder_and_check(tags[self.FOLDER_TAG_NAME])
            resource.folder = folder

        if tags and tags.get(self.NAME_TAG_NAME):
            resource.name = tags[self.NAME_TAG_NAME]

        return resource

    def get_additional_tags(self, tags: Dict[str, str]) -> Dict[str, str]:
        """Return the additional tags to save on the object, it skips the predefined tags
        """
        cleaned_tags = {}
        for key, value in tags.items():
            # skip predefined tags
            if key in [self.STORAGE_TAG_NAME, self.BUCKET_TAG_NAME, self.KEY_TAG_NAME,
                       self.FOLDER_TAG_NAME, self.NAME_TAG_NAME]:
                continue
            cleaned_tags[key] = value
        return cleaned_tags

    def get_tag_origin(self) -> TagOrigins:
        """Get the origin of a tag
        """
        return TagOrigins(TagOriginType.S3, 's3')

    def get_datahub_tag(self) -> Tag:
        """Get the datahub tag used to tags the objects that are stored in the datahub

        :return: _description_
        :rtype: Tag
        """
        return Tag(self.BUCKET_TAG_NAME, self.FOLDERS_BUCKET_NAME)

    ##################################################### MULTIPART UPLOAD METHODS #####################################################

    def initiate_multipart_upload(self, key: str, last_modified: float = None) -> str:
        """Initiate a multipart upload and return upload ID"""
        raise NotImplementedError("Multipart upload is not supported in DataHub S3 service")

    def upload_part(self, key: str, upload_id: str, part_number: int, data: ByteString) -> str:
        """Upload a part for multipart upload and return ETag"""
        raise NotImplementedError("Multipart upload is not supported in DataHub S3 service")

    def complete_multipart_upload(self, key: str, upload_id: str, parts: List[dict]) -> str:
        """Complete multipart upload and return ETag"""
        raise NotImplementedError("Multipart upload is not supported in DataHub S3 service")

    def abort_multipart_upload(self, key: str, upload_id: str) -> None:
        """Abort a multipart upload and clean up temp files"""
        raise NotImplementedError("Multipart upload is not supported in DataHub S3 service")

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

    @staticmethod
    def get_instance() -> 'DataHubS3ServerService':
        """Get an instance of the DataHubS3ServerService

        :param bucket_name: the bucket name
        :return: the instance of the service
        """
        return DataHubS3ServerService(bucket_name=DataHubS3ServerService.FOLDERS_BUCKET_NAME)

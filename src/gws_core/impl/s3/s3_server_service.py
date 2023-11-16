# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from os import path
from typing import ByteString, Optional

from fastapi.responses import FileResponse
from mypy_boto3_s3.type_defs import ListObjectsV2OutputTypeDef, ObjectTypeDef

from gws_core.core.decorator.transaction import transaction
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file import File
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.s3.s3_server_exception import (S3ServerContext,
                                                  S3ServerException,
                                                  S3ServerNoSuchKey)
from gws_core.project.project import Project
from gws_core.resource.resource_model import ResourceModel, ResourceOrigin
from gws_core.resource.resource_model_search_builder import \
    ResourceModelSearchBuilder
from gws_core.resource.resource_service import ResourceService
from gws_core.tag.entity_tag import EntityTag, EntityTagType
from gws_core.tag.tag import Tag
from gws_core.tag.tag_service import TagService
from gws_core.user.current_user_service import CurrentUserService
from gws_core.user.user import User


class S3ServerService:
    """Class to manage file upload to this lab as an S3 server
    """

    # defaumlt bucket name for projects storage
    PROJECTS_BUCKET_NAME = 'projects-storage'

    @classmethod
    def create_bucket(cls, bucket_name: str) -> None:
        if not cls._is_project_doc_bucket(bucket_name):
            raise S3ServerException(status_code=400, code='invalid_bucket_name',
                                    message='Invalid bucket name, only project storage is allowed for now',
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
                'Contents': bucket_objects
            }

    @classmethod
    @transaction()
    def upload_object(cls, bucket_name: str,
                      key: str, data: ByteString) -> None:
        """Upload an object to the bucket
        """

        project: Project = None
        if cls._is_project_doc_bucket(bucket_name):
            project = cls._get_and_check_project_bucket(bucket_name, key)
        else:
            # for now we allow only project documents to be uploaded
            raise S3ServerException(status_code=400, code='invalid_bucket_name',
                                    message='Invalid bucket name, only project storage is allowed for now',
                                    bucket_name=bucket_name, key=key)

        # check if it already exists
        resource_model = cls._get_object(bucket_name, key)

        if resource_model:
            raise S3ServerException(status_code=400, code='object_exists', message='Object already exists',
                                    bucket_name=bucket_name, key=key)

        with S3ServerContext(bucket_name, key):
            # create a file in a temp folder
            temp_folder = Settings.make_temp_dir()

            filename = FileHelper.get_name_with_extension(key)
            file_path = path.join(temp_folder, filename)
            with open(file_path, 'wb') as write_file:
                write_file.write(data)

            # make a resource from the file
            file = File(file_path)

            resource_origin = ResourceOrigin.S3_PROJECT_STORAGE if cls._is_project_doc_bucket(
                bucket_name) else ResourceOrigin.UPLOADED

            resource_model = ResourceModel.from_resource(file, resource_origin)
            resource_model.name = FileHelper.get_name_with_extension(key)
            resource_model.project = project

            # Authenticate sys user because in S3 server we don't have a user
            CurrentUserService.set_current_user(User.get_sysuser())
            try:
                resource_model = resource_model.save_full()
                TagService.add_tags_to_entity(
                    EntityTagType.RESOURCE, resource_model.id,
                    [Tag('storage', 's3'),
                     Tag('bucket', bucket_name),
                     Tag('key', key)])
            finally:
                CurrentUserService.set_current_user(None)

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
        resource: ResourceModel = cls._get_object_and_check(bucket_name, key)

        with S3ServerContext(bucket_name, key):
            # Authenticate sys user because in S3 server we don't have a user
            CurrentUserService.set_current_user(User.get_sysuser())
            try:
                ResourceService.delete(resource_id=resource.id, allow_s3_project_storage=True)
            finally:
                CurrentUserService.set_current_user(None)

    @classmethod
    def head_object(cls, bucket_name: str, key: str) -> None:
        """Head an object from the bucket
        """
        cls._get_object_and_check(bucket_name, key)

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

        if cls._is_project_doc_bucket(bucket_name):
            cls._get_and_check_project_bucket(bucket_name, key)

        resource: ResourceModel = cls._get_object(bucket_name, key)

        if resource is None:
            raise S3ServerNoSuchKey(bucket_name, key)

        return resource

    @classmethod
    def _is_project_doc_bucket(cls, bucket_name: str) -> bool:
        """Check if the bucket is the project document bucket
        """
        return bucket_name == cls.PROJECTS_BUCKET_NAME

    @classmethod
    def _get_and_check_project_bucket(cls, bucket_name: str, key_or_prefix: str) -> Project:
        """Get a project bucket
        """
        if not cls._is_project_doc_bucket(bucket_name):
            raise S3ServerException(status_code=400, code='invalid_bucket_name',
                                    message='Invalid bucket name',
                                    bucket_name=bucket_name, key=key_or_prefix)

        # extract the project name from the key
        # format of the key : <space_id>/<root_project_id>/<project_id>/documents/<file_name>
        key_parts = key_or_prefix.split('/')
        if len(key_parts) < 3:
            raise S3ServerException(status_code=400, code='invalid_key',
                                    message='Invalid key',
                                    bucket_name=bucket_name, key=key_or_prefix)

        project: Project = Project.get_by_id(key_parts[2])

        if project is None:
            raise S3ServerException(status_code=400, code='invalid_project_id',
                                    message='Project not found in lab, try to sync the lab projects',
                                    bucket_name=bucket_name, key=key_or_prefix)

        return project

    @classmethod
    def _resource_to_s3_object(cls, resource: ResourceModel) -> ObjectTypeDef:
        entity_tag: EntityTag = EntityTag.find_by_tag_key_and_entity('key', resource.id, EntityTagType.RESOURCE).first()
        if not entity_tag:
            raise S3ServerException(status_code=500, code='invalid_resource',
                                    message='Resource has no key tag', bucket_name='')
        return {
            'Key': entity_tag.tag_value,
            'LastModified': resource.last_modified_at,
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

        search_builder.add_tag_filter(Tag('storage', 's3'))
        search_builder.add_tag_filter(Tag('bucket', bucket_name))

        search_builder.add_expression(ResourceModel.fs_node_model.is_null(False))

        if cls._is_project_doc_bucket(bucket_name):
            search_builder.add_expression(ResourceModel.origin == ResourceOrigin.S3_PROJECT_STORAGE)
        else:
            search_builder.add_expression(ResourceModel.origin == ResourceOrigin.UPLOADED)

        if key:
            search_builder.add_tag_filter(Tag('key', key))

        if prefix:
            if not prefix.endswith('/'):
                prefix += '/'
            search_builder.add_tag_filter(Tag('key', prefix), 'START_WITH')

        return search_builder

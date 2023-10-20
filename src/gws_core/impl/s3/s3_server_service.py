# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from os import path
from typing import ByteString

from fastapi.responses import FileResponse

from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file import File
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.s3.s3_dto import BucketObject, ListBucketResult
from gws_core.resource.resource_model import ResourceModel, ResourceOrigin
from gws_core.resource.resource_service import ResourceService
from gws_core.tag.tag import Tag


class S3ServerService:
    """Class to manage file upload to this lab as an S3 server
    """

    @classmethod
    def list_objects(cls, bucket_name: str, prefix: str = None, max_keys: int = 1000) -> ListBucketResult:
        """List objects in a bucket
        """

        # TODO add support for prefix and max_keys
        tags = [Tag('storage', 's3'), Tag('bucket', bucket_name)]
        resources = ResourceModel.select().where(
            (ResourceModel.get_search_tag_expression(tags)) &
            (ResourceModel.fs_node_model.is_null(False)) &
            (ResourceModel.origin == ResourceOrigin.UPLOADED)).order_by(ResourceModel.name)

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
    def upload_object(cls, bucket_name: str, key: str, data: ByteString) -> None:
        """Upload an object to the bucket
        """
        # create a file in a temp folder
        temp_folder = Settings.make_temp_dir()

        file_path = path.join(temp_folder, key)
        with open(file_path, 'wb') as write_file:
            write_file.write(data)

        # make a resource from the file
        file = File(file_path)

        resource_model = ResourceModel.from_resource(file, ResourceOrigin.UPLOADED)
        resource_model.set_tags([Tag('storage', 's3'), Tag('bucket', bucket_name)])
        resource_model.save_full()

    @classmethod
    def get_object(cls, bucket_name: str, key: str) -> FileResponse:
        """Get an object from the bucket
        """
        # TODO handle errors
        resource: ResourceModel = cls._get_object(bucket_name, key)

        return FileHelper.create_file_response(resource.fs_node_model.path)

    @classmethod
    def delete_object(cls, bucket_name: str, key: str) -> None:
        """Delete an object from the bucket
        """
        # TODO handle errors
        resource: ResourceModel = cls._get_object(bucket_name, key)

        ResourceService.delete(resource_id=resource.id)

    @classmethod
    def _get_object(cls, bucket_name: str, key: str) -> ResourceModel:
        """Get an object from the bucket
        """
        # TODO handle errors
        resource: ResourceModel = ResourceModel.get_by_id_and_check(key)

        if not resource:
            raise Exception('Resource not found')

        if resource.origin != ResourceOrigin.UPLOADED:
            raise Exception('Resource not uploaded')

        if not resource.has_tag(Tag('storage', 's3')) or not resource.has_tag(Tag('bucket', bucket_name)):
            raise Exception('Resource not in bucket')

        return resource

    @classmethod
    def _resource_to_s3_object(cls, resource: ResourceModel) -> BucketObject:
        return {
            'Key': resource.id,
            'LastModified': DateHelper.to_iso_str(resource.last_modified_at),
            'ETag': '',
            'Size': resource.fs_node_model.size,
            'Owner': {
                'ID': '',
                'DisplayName': 'lab'
            },
            'StorageClass': 'STANDARD'
        }

import os
from os import path
from typing import ByteString, Dict, List

from fastapi.responses import FileResponse
from mypy_boto3_s3.type_defs import ListObjectsV2OutputTypeDef, ObjectTypeDef

from gws_core.core.utils.date_helper import DateHelper
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.s3.abstract_s3_service import AbstractS3Service
from gws_core.impl.s3.s3_server_dto import S3GetTagResponse, S3UpdateTagRequest
from gws_core.impl.s3.s3_server_exception import S3ServerNoSuchKey


class LocalS3ServerService(AbstractS3Service):
    """Local S3 service that stores files in a local directory"""

    bucket_path: str

    def __init__(self, bucket_name: str, bucket_path: str):
        """Initialize the service with a bucket name"""
        super().__init__(bucket_name)
        self.bucket_path = bucket_path

    def create_bucket(self) -> None:
        """Create a bucket (directory) in the local filesystem"""
        os.makedirs(self.bucket_path, exist_ok=True)

    def list_objects(self, prefix: str = None, max_keys: int = 1000, delimiter: str = None) -> ListObjectsV2OutputTypeDef:
        """List objects in a bucket"""
        if not path.exists(self.bucket_path):
            return {
                'Name': self.bucket_name,
                'Prefix': prefix or '',
                'MaxKeys': max_keys,
                'IsTruncated': False,
                'Contents': [],
                'KeyCount': 0,
                'ContinuationToken': '',
                'NextContinuationToken': '',
                'StartAfter': '',
                'Delimiter': delimiter or '',
                'EncodingType': 'url',
                'RequestCharged': 'requester',
                'CommonPrefixes': [],
                'ResponseMetadata': {
                    'RequestId': '',
                    'HTTPStatusCode': 200,
                    'HTTPHeaders': {},
                    'RetryAttempts': 0
                },
            }

        objects: List[ObjectTypeDef] = []
        common_prefixes = set()

        # Get all files in the bucket
        all_keys = []
        for root, _, files in os.walk(self.bucket_path):
            for file in files:
                file_path = path.join(root, file)
                relative_path = path.relpath(file_path, self.bucket_path)
                key = relative_path.replace(os.sep, '/')
                all_keys.append((key, file_path))

        # Filter by prefix if provided
        if prefix:
            all_keys = [(key, file_path) for key, file_path in all_keys if key.startswith(prefix)]

        # Process keys based on delimiter
        for key, file_path in all_keys:
            if delimiter:
                # Find the next delimiter after the prefix
                search_start = len(prefix) if prefix else 0
                delimiter_pos = key.find(delimiter, search_start)

                if delimiter_pos != -1:
                    # This is in a subdirectory, add to common prefixes
                    common_prefix = key[:delimiter_pos + 1]
                    common_prefixes.add(common_prefix)
                    continue

            # Add as regular object
            if len(objects) < max_keys:
                stat = os.stat(file_path)
                last_modified = DateHelper.from_utc_milliseconds(int(stat.st_mtime * 1000))
                objects.append({
                    'Key': key,
                    'LastModified': DateHelper.to_iso_str(last_modified),
                    'ETag': '',
                    'Size': stat.st_size,
                    'Owner': {
                        'ID': '',
                        'DisplayName': 'lab'
                    },
                    'StorageClass': 'STANDARD'
                })

        # Convert common prefixes to the expected format
        common_prefixes_list = [{'Prefix': cp} for cp in sorted(common_prefixes)]

        return {
            'Name': self.bucket_name,
            'Prefix': prefix or '',
            'MaxKeys': max_keys,
            'IsTruncated': len(objects) >= max_keys,
            'Contents': objects,
            'KeyCount': len(objects),
            'ContinuationToken': '',
            'NextContinuationToken': '',
            'StartAfter': '',
            'Delimiter': delimiter or '',
            'EncodingType': 'url',
            'RequestCharged': 'requester',
            'CommonPrefixes': common_prefixes_list,
            'ResponseMetadata': {
                'RequestId': '',
                'HTTPStatusCode': 200,
                'HTTPHeaders': {},
                'RetryAttempts': 0
            },
        }

    def upload_object(self, key: str, data: ByteString, tags: Dict[str, str] = None) -> None:
        """Upload an object to the bucket"""
        self.create_bucket()

        file_path = path.join(self.bucket_path, key)
        os.makedirs(path.dirname(file_path), exist_ok=True)

        with open(file_path, 'wb') as f:
            f.write(data)

    def get_object(self, key: str) -> FileResponse:
        """Get an object from the bucket"""
        file_path = path.join(self.bucket_path, key)

        if not path.exists(file_path):
            raise S3ServerNoSuchKey(self.bucket_name, key)

        return FileResponse(file_path)

    def delete_object(self, key: str) -> None:
        """Delete an object from the bucket"""
        file_path = path.join(self.bucket_path, key)

        if path.exists(file_path):
            os.remove(file_path)

    def delete_objects(self, keys: List[str]) -> None:
        """Delete multiple objects"""
        for key in keys:
            try:
                self.delete_object(key)
            except S3ServerNoSuchKey:
                pass

    def head_object(self, key: str) -> dict:
        """Head an object from the bucket"""
        file_path = path.join(self.bucket_path, key)

        if not path.exists(file_path):
            raise S3ServerNoSuchKey(self.bucket_name, key)

        stat = os.stat(file_path)
        last_modified = DateHelper.from_utc_milliseconds(int(stat.st_mtime * 1000))
        return {
            'Content-Length': str(stat.st_size),
            'Content-Type': FileHelper.get_mime(file_path),
            'Last-Modified': DateHelper.to_rfc7231_str(last_modified),
        }

    def get_object_tags(self, key: str) -> S3GetTagResponse:
        """Get the tags of an object"""
        raise NotImplementedError("Tagging is not supported in basic S3 service")

    def update_object_tags(self, key: str, tags: S3UpdateTagRequest) -> None:
        """Update the tags of an object"""
        raise NotImplementedError("Tagging is not supported in basic S3 service")

    def update_object_tags_dict(self, key: str, tags: Dict[str, str]) -> None:
        """Update the tags of an object with a dictionary"""
        raise NotImplementedError("Tagging is not supported in basic S3 service")

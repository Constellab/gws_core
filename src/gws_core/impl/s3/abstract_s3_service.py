from abc import ABC, abstractmethod
from typing import ByteString, Dict, List

from fastapi.responses import FileResponse
from mypy_boto3_s3.type_defs import ListObjectsV2OutputTypeDef

from gws_core.impl.s3.s3_server_dto import S3GetTagResponse, S3UpdateTagRequest


class AbstractS3Service(ABC):
    """Abstract base class for S3 services"""

    def __init__(self, bucket_name: str):
        """Initialize the service with a bucket name"""
        self.bucket_name = bucket_name

    @abstractmethod
    def create_bucket(self) -> None:
        """Create a bucket"""

    @abstractmethod
    def list_objects(self, prefix: str = None, max_keys: int = 1000, delimiter: str = None,
                     continuation_token: str = None, start_after: str = None) -> ListObjectsV2OutputTypeDef:
        """List objects in a bucket"""

    @abstractmethod
    def upload_object(self, key: str, data: ByteString, tags: Dict[str, str] = None,
                      last_modified: float = None) -> dict:
        """Upload an object to the bucket"""

    @abstractmethod
    def get_object(self, key: str) -> FileResponse:
        """Get an object from the bucket"""

    @abstractmethod
    def delete_object(self, key: str) -> None:
        """Delete an object from the bucket"""

    @abstractmethod
    def delete_objects(self, keys: List[str]) -> None:
        """Delete multiple objects"""

    @abstractmethod
    def head_object(self, key: str) -> dict:
        """Head an object from the bucket"""

    @abstractmethod
    def get_object_tags(self, key: str) -> S3GetTagResponse:
        """Get the tags of an object"""

    @abstractmethod
    def update_object_tags(self, key: str, tags: S3UpdateTagRequest) -> None:
        """Update the tags of an object"""

    @abstractmethod
    def update_object_tags_dict(self, key: str, tags: Dict[str, str]) -> None:
        """Update the tags of an object with a dictionary"""

    @abstractmethod
    def initiate_multipart_upload(self, key: str, last_modified: float = None) -> str:
        """Initiate a multipart upload and return upload ID"""

    @abstractmethod
    def upload_part(self, key: str, upload_id: str, part_number: int, data: ByteString) -> str:
        """Upload a part for multipart upload and return ETag"""

    @abstractmethod
    def complete_multipart_upload(self, key: str, upload_id: str, parts: List[dict]) -> str:
        """Complete multipart upload and return ETag"""

    @abstractmethod
    def abort_multipart_upload(self, key: str, upload_id: str) -> None:
        """Abort a multipart upload and clean up temp files"""

    @staticmethod
    def convert_query_param_string_to_dict(query_param: str) -> dict:
        """Convert a query parameter string to a dictionary"""
        if not query_param:
            return {}

        return dict([param.split('=') for param in query_param.split('&')])

import json
import os
import time
import uuid
from collections.abc import ByteString
from os import path
from typing import Any

from fastapi.responses import FileResponse
from mypy_boto3_s3.type_defs import ListObjectsV2OutputTypeDef

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

    @property
    def _multipart_state_file(self) -> str:
        """Path to multipart upload state file"""
        return path.join(self.bucket_path, ".multipart", "state.json")

    def _load_multipart_state(self) -> dict[str, Any]:
        """Load multipart upload state from disk"""
        if not path.exists(self._multipart_state_file):
            return {}
        try:
            with open(self._multipart_state_file) as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_multipart_state(self, state: dict[str, Any]) -> None:
        """Save multipart upload state to disk"""
        multipart_dir = path.dirname(self._multipart_state_file)

        if state:
            # Save state if not empty
            os.makedirs(multipart_dir, exist_ok=True)
            with open(self._multipart_state_file, "w") as f:
                json.dump(state, f)
        else:
            # Clean up when state is empty
            # Remove state file if it exists
            if path.exists(self._multipart_state_file):
                os.remove(self._multipart_state_file)

            # Remove .multipart directory if it's empty
            if path.exists(multipart_dir):
                try:
                    # Check if directory is empty (no files, no subdirectories)
                    if not any(os.scandir(multipart_dir)):
                        os.rmdir(multipart_dir)
                except OSError:
                    # Directory not empty or other error, leave it
                    pass

    def list_objects(
        self,
        prefix: str = None,
        max_keys: int = 1000,
        delimiter: str = None,
        continuation_token: str = None,
        start_after: str = None,
    ) -> ListObjectsV2OutputTypeDef:
        """List objects in a bucket"""
        if not path.exists(self.bucket_path):
            return {
                "Name": self.bucket_name,
                "Prefix": prefix or "",
                "MaxKeys": max_keys,
                "IsTruncated": False,
                "Contents": [],
                "KeyCount": 0,
                "ContinuationToken": "",
                "NextContinuationToken": "",
                "StartAfter": "",
                "Delimiter": delimiter or "",
                "EncodingType": "url",
                "RequestCharged": "requester",
                "CommonPrefixes": [],
                "ResponseMetadata": {
                    "RequestId": "",
                    "HTTPStatusCode": 200,
                    "HTTPHeaders": {},
                    "RetryAttempts": 0,
                },
            }

        objects: list[Any] = []
        common_prefixes = set()

        # Get all files in the bucket
        all_keys = []
        for root, _, files in os.walk(self.bucket_path):
            for file in files:
                file_path = path.join(root, file)
                relative_path = path.relpath(file_path, self.bucket_path)
                key = relative_path.replace(os.sep, "/")
                all_keys.append((key, file_path))

        # Filter by prefix if provided
        if prefix:
            all_keys = [(key, file_path) for key, file_path in all_keys if key.startswith(prefix)]

        # Sort keys for consistent pagination
        all_keys.sort(key=lambda x: x[0])

        # Apply start_after filter
        if start_after:
            all_keys = [(key, file_path) for key, file_path in all_keys if key > start_after]

        # Apply continuation_token filter (continuation_token is the last key from previous page)
        if continuation_token:
            all_keys = [(key, file_path) for key, file_path in all_keys if key > continuation_token]

        # Process keys based on delimiter and collect results
        processed_objects = []
        for key, file_path in all_keys:
            if delimiter:
                # Find the next delimiter after the prefix
                search_start = len(prefix) if prefix else 0
                delimiter_pos = key.find(delimiter, search_start)

                if delimiter_pos != -1:
                    # This is in a subdirectory, add to common prefixes
                    common_prefix = key[: delimiter_pos + 1]
                    common_prefixes.add(common_prefix)
                    continue

            # Add as regular object
            stat = os.stat(file_path)
            last_modified = DateHelper.from_utc_milliseconds(int(stat.st_mtime * 1000))
            processed_objects.append(
                {
                    "Key": key,
                    "LastModified": DateHelper.to_iso_str(last_modified),
                    "ETag": "",
                    "Size": stat.st_size,
                    "Owner": {"ID": "", "DisplayName": "lab"},
                    "StorageClass": "STANDARD",
                }
            )

        # Apply pagination to processed objects
        is_truncated = len(processed_objects) > max_keys
        objects = processed_objects[:max_keys]
        next_continuation_token = ""

        if is_truncated and objects:
            next_continuation_token = objects[-1]["Key"]

        # Convert common prefixes to the expected format
        common_prefixes_list: list[Any] = [{"Prefix": cp} for cp in sorted(common_prefixes)]

        return {
            "Name": self.bucket_name,
            "Prefix": prefix or "",
            "MaxKeys": max_keys,
            "IsTruncated": is_truncated,
            "Contents": objects,
            "KeyCount": len(objects),
            "ContinuationToken": continuation_token or "",
            "NextContinuationToken": next_continuation_token,
            "StartAfter": start_after or "",
            "Delimiter": delimiter or "",
            "EncodingType": "url",
            "RequestCharged": "requester",
            "CommonPrefixes": common_prefixes_list,
            "ResponseMetadata": {
                "RequestId": "",
                "HTTPStatusCode": 200,
                "HTTPHeaders": {},
                "RetryAttempts": 0,
            },
        }

    def upload_object(
        self, key: str, data: ByteString, tags: dict[str, str] = None, last_modified: float = None
    ) -> dict:
        """Upload an object to the bucket"""
        del tags  # Unused parameter
        self.create_bucket()

        file_path = path.join(self.bucket_path, key)
        os.makedirs(path.dirname(file_path), exist_ok=True)

        with open(file_path, "wb") as f:
            f.write(data)

        if last_modified:
            # Set the modification time if provided
            os.utime(file_path, (last_modified, last_modified))

        return {
            "ETag": "",
        }

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

    def delete_objects(self, keys: list[str]) -> None:
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
            "Content-Length": "0" if FileHelper.is_dir(file_path) else str(stat.st_size),
            "Content-Type": FileHelper.get_mime(file_path),
            "Last-Modified": DateHelper.to_rfc7231_str(last_modified),
            "x-amz-meta-mtime": str(stat.st_mtime),  # rclone compatibility
        }

    def get_object_tags(self, key: str) -> S3GetTagResponse:
        """Get the tags of an object"""
        del key  # Unused parameter
        raise NotImplementedError("Tagging is not supported in basic S3 service")

    def update_object_tags(self, key: str, tags: S3UpdateTagRequest) -> None:
        """Update the tags of an object"""
        del key, tags  # Unused parameters
        raise NotImplementedError("Tagging is not supported in basic S3 service")

    def update_object_tags_dict(self, key: str, tags: dict[str, str]) -> None:
        """Update the tags of an object with a dictionary"""
        del key, tags  # Unused parameters
        raise NotImplementedError("Tagging is not supported in basic S3 service")

    def initiate_multipart_upload(self, key: str, last_modified: float = None) -> str:
        """Initiate a multipart upload and return upload ID"""
        # Clean up old uploads before starting new one
        self._cleanup_abandoned_uploads()

        upload_id = str(uuid.uuid4())

        # Create temp directory for parts
        temp_dir = path.join(self.bucket_path, ".multipart", upload_id)
        os.makedirs(temp_dir, exist_ok=True)

        # Load current state and add new upload
        state = self._load_multipart_state()
        state[upload_id] = {
            "key": key,
            "parts": {},
            "temp_dir": temp_dir,
            "last_modified": last_modified,
            "created_at": time.time(),
        }
        self._save_multipart_state(state)

        return upload_id

    def upload_part(self, key: str, upload_id: str, part_number: int, data: ByteString) -> None:
        """Upload a part for multipart upload and return ETag"""
        state = self._load_multipart_state()
        if upload_id not in state:
            raise ValueError(f"Upload ID {upload_id} not found")

        upload_info = state[upload_id]
        if upload_info["key"] != key:
            raise ValueError(f"Key mismatch for upload ID {upload_id}")

        # Save part to temp file
        part_file = path.join(upload_info["temp_dir"], f"part_{part_number:05d}")
        with open(part_file, "wb") as f:
            f.write(data)

        # Store part info
        upload_info["parts"][str(part_number)] = {"etag": "", "file": part_file, "size": len(data)}

        # Save updated state
        self._save_multipart_state(state)

    def complete_multipart_upload(self, key: str, upload_id: str, parts: list[dict]) -> None:
        """Complete multipart upload and return ETag"""
        state = self._load_multipart_state()
        if upload_id not in state:
            raise ValueError(f"Upload ID {upload_id} not found")

        upload_info = state[upload_id]
        if upload_info["key"] != key:
            raise ValueError(f"Key mismatch for upload ID {upload_id}")

        # Sort parts by part number
        sorted_parts = sorted(parts, key=lambda p: int(p["PartNumber"]))

        # Create final file
        self.create_bucket()
        file_path = path.join(self.bucket_path, key)
        os.makedirs(path.dirname(file_path), exist_ok=True)

        # Combine all parts and calculate MD5 hash incrementally
        with open(file_path, "wb") as final_file:
            for part in sorted_parts:
                part_number = str(part["PartNumber"])
                if part_number not in upload_info["parts"]:
                    raise ValueError(f"Part {part_number} not found")

                part_file = upload_info["parts"][part_number]["file"]
                with open(part_file, "rb") as pf:
                    # Read and write in chunks to avoid memory issues
                    while True:
                        chunk = pf.read(8192)  # 8KB chunks
                        if not chunk:
                            break
                        final_file.write(chunk)

        # Apply modification time if provided
        if upload_info.get("last_modified"):
            # Set the modification time if provided
            os.utime(file_path, (upload_info["last_modified"], upload_info["last_modified"]))

        # Clean up temp files using helper method
        self._cleanup_upload_files(upload_info)

        # Remove from active uploads
        del state[upload_id]
        self._save_multipart_state(state)

    def _cleanup_abandoned_uploads(self, max_age_hours: int = 24) -> None:
        """Clean up abandoned multipart uploads older than max_age_hours"""
        try:
            state = self._load_multipart_state()
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600

            uploads_to_remove = []

            for upload_id, upload_info in state.items():
                # Check if temp directory exists and get its age
                temp_dir = upload_info.get("temp_dir")
                if temp_dir and path.exists(temp_dir):
                    dir_age = current_time - path.getctime(temp_dir)
                    if dir_age > max_age_seconds:
                        uploads_to_remove.append(upload_id)
                        # Clean up temp files
                        self._cleanup_upload_files(upload_info)
                elif temp_dir:
                    # Temp directory doesn't exist, remove from state
                    uploads_to_remove.append(upload_id)

            # Remove abandoned uploads from state
            for upload_id in uploads_to_remove:
                del state[upload_id]

            if uploads_to_remove:
                self._save_multipart_state(state)

        except Exception:
            # Don't let cleanup errors break normal operations
            pass

    def _cleanup_upload_files(self, upload_info: dict[str, Any]) -> None:
        """Clean up files for a specific upload"""
        try:
            # Clean up individual part files
            for part_info in upload_info.get("parts", {}).values():
                part_file = part_info.get("file")
                if part_file and path.exists(part_file):
                    os.remove(part_file)

            # Remove temp directory if empty
            temp_dir = upload_info.get("temp_dir")
            if temp_dir and path.exists(temp_dir):
                try:
                    os.rmdir(temp_dir)
                except OSError:
                    # Directory not empty, leave it
                    pass
        except Exception:
            # Don't let cleanup errors break normal operations
            pass

    def abort_multipart_upload(self, key: str, upload_id: str) -> None:
        """Abort a multipart upload and clean up temp files"""
        state = self._load_multipart_state()
        if upload_id not in state:
            raise ValueError(f"Upload ID {upload_id} not found")

        upload_info = state[upload_id]
        if upload_info["key"] != key:
            raise ValueError(f"Key mismatch for upload ID {upload_id}")

        # Clean up temp files
        self._cleanup_upload_files(upload_info)

        # Remove from state
        del state[upload_id]
        self._save_multipart_state(state)

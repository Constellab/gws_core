import time
from typing import TypedDict

import boto3
from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file_helper import FileHelper
from mypy_boto3_s3.client import S3Client


class S3BucketActionProgress(TypedDict):
    transfered_bytes: int
    last_progress: int


class S3Bucket:
    """
    S3Bucket class is a wrapper around boto3 S3 client to provide a simplified interface to upload and download files
    to and from an S3 bucket.

    :raises Exception: _description_
    :return: _description_
    :rtype: _type_
    """

    endpoint: str
    region: str
    access_key_id: str
    secret_access_key: str
    bucket_name: str

    message_dispatcher: MessageDispatcher

    def __init__(
        self,
        endpoint: str,
        region: str,
        access_key_id: str,
        secret_access_key: str,
        bucket_name: str,
        message_dispatcher: MessageDispatcher = None,
    ):
        """

        :param endpoint: url of the S3 endpoint
        :type endpoint: str
        :param region: region of the S3 bucket
        :type region: str
        :param access_key_id: access key id
        :type access_key_id: str
        :param secret_access_key: secret access key
        :type secret_access_key: str
        :param bucket_name: name of the S3 bucket
        :type bucket_name: str
        :param message_dispatcher: a message dispatcher can be provided (from a task for example) to notify the progress of the upload/download
        :type message_dispatcher: MessageDispatcher, optional
        """
        self.endpoint = endpoint
        self.region = region
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.bucket_name = bucket_name

        if message_dispatcher:
            self.message_dispatcher = message_dispatcher
        else:
            self.message_dispatcher = MessageDispatcher()

    def upload_file(self, file_path: str, object_key: str) -> None:
        if not FileHelper.exists_on_os(file_path):
            raise Exception(f"File {file_path} does not exists")

        mime_type = FileHelper.get_mime(file_path)
        total_size = FileHelper.get_size(file_path)

        upload_progress: S3BucketActionProgress = {"transfered_bytes": 0, "last_progress": 0}

        start_time = time.time()

        s3_client = self._get_s3_bucket()

        self.message_dispatcher.notify_info_message(
            f"Uploading file to S3 bucket '{self.bucket_name}', object key '{object_key}'"
        )

        s3_client.upload_file(
            file_path,
            self.bucket_name,
            object_key,
            ExtraArgs={"ContentType": mime_type},
            Callback=lambda progress: self._upload_progress_callback(
                progress, total_size, start_time, upload_progress, "Uploaded"
            ),
        )

        duration = DateHelper.get_duration_pretty_text(time.time() - start_time)
        self.message_dispatcher.notify_success_message(
            f"File '{object_key}' uploaded to bucket '{self.bucket_name}' in {duration}"
        )

    def get_object(self, object_key: str, local_file_path: str = None) -> str:
        bucket = self._get_s3_bucket()

        if local_file_path is None:
            temp_dir = Settings.make_temp_dir()
            local_file_path = f"{temp_dir}/{FileHelper.get_name_with_extension(object_key)}"

        upload_progress: S3BucketActionProgress = {"transfered_bytes": 0, "last_progress": 0}

        self.message_dispatcher.notify_info_message(
            f"Retrieving information for S3 object '{object_key}' from bucket '{self.bucket_name}'"
        )
        response = bucket.head_object(Bucket=self.bucket_name, Key=object_key)
        total_size = response["ContentLength"]

        start_time = time.time()
        self.message_dispatcher.notify_info_message(
            f"Downloading S3 object '{object_key}' from  bucket '{self.bucket_name}'"
        )

        bucket.download_file(
            self.bucket_name,
            object_key,
            local_file_path,
            Callback=lambda chunk: self._upload_progress_callback(
                chunk, total_size, start_time, upload_progress, "Downloaded"
            ),
        )

        duration = DateHelper.get_duration_pretty_text(time.time() - start_time)
        self.message_dispatcher.notify_success_message(
            f"File downloaded to '{local_file_path}' from bucket '{self.bucket_name}' in {duration}"
        )

        return local_file_path

    def _upload_progress_callback(
        self,
        transfered_bytes: int,
        total_size: int,
        start_time: float,
        action_progress: S3BucketActionProgress,
        action_name: str,
    ) -> None:
        action_progress["transfered_bytes"] += transfered_bytes
        progress = int(action_progress["transfered_bytes"] / total_size * 100)

        # log progress every 3%
        if progress - action_progress["last_progress"] > 3:
            action_progress["last_progress"] = progress
            transfered_str = FileHelper.get_file_size_pretty_text(
                action_progress["transfered_bytes"]
            )
            total_str = FileHelper.get_file_size_pretty_text(total_size)
            # calculate remaining time
            remaining_time = (time.time() - start_time) / (
                action_progress["transfered_bytes"] / total_size
            ) - (time.time() - start_time)

            remaining_time_str = DateHelper.get_duration_pretty_text(remaining_time)

            self.message_dispatcher.notify_progress_value(
                progress,
                f"{action_name} {transfered_str}/{total_str} ({progress}%) - {remaining_time_str} remaining",
            )

    def _get_s3_bucket(self) -> S3Client:
        return boto3.client(
            "s3",
            endpoint_url=self.endpoint,
            region_name=self.region,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
        )
        # return s3.Bucket(self.bucket_name)

# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import time

import boto3

from gws_core.config.param.param_spec import BoolParam, StrParam
from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.string_helper import StringHelper
from gws_core.impl.file.file_helper import FileHelper
from gws_core.io.io_spec import InputSpec
from gws_core.resource.resource_zipper import ResourceZipper
from gws_core.space.mail_service import MailService
from gws_core.user.current_user_service import CurrentUserService

from ...config.config_types import ConfigParams, ConfigSpecs
from ...io.io_spec_helper import InputSpecs, OutputSpecs
from ...resource.resource import Resource
from ...task.task import Task
from ...task.task_decorator import task_decorator
from ...task.task_io import TaskInputs, TaskOutputs


@task_decorator(unique_name="SendResourceToS3", human_name="Send resource to S3",
                short_description="Simple task to send the input resource to a S3 bucket")
class SendResourceToS3(Task):
    input_specs: InputSpecs = {'resource': InputSpec(Resource)}
    output_specs: OutputSpecs = {}
    config_specs: ConfigSpecs = {
        's3_endpoint': StrParam(human_name="S3 endpoint"),
        's3_region': StrParam(human_name="S3 region"),
        's3_access_key_id': StrParam(human_name="S3 access key id"),
        's3_secret_access_key': StrParam(human_name="S3 secret access key"),
        's3_bucket': StrParam(human_name="S3 bucket name"),
        's3_object_prefix': StrParam(human_name="Prefix for the S3 object"),
        'send_me_an_email': BoolParam(human_name="Send me an email when the task is finished", default_value=False)
    }

    zip_file_path: str = None
    transfered_bytes: int = 0
    last_progress: int = 0

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        bucket_name = params.get_value('s3_bucket')

        self.log_info_message('Zipping resource')
        resource: Resource = inputs['resource']
        resource_zipper = ResourceZipper(CurrentUserService.get_current_user())
        resource_zipper.add_resource(resource)
        self.zip_file_path = resource_zipper.close_zip()

        s3 = boto3.resource('s3',
                            endpoint_url=params.get_value('s3_endpoint'),
                            region_name=params.get_value('s3_region'),
                            aws_access_key_id=params.get_value('s3_access_key_id'),
                            aws_secret_access_key=params.get_value('s3_secret_access_key'))
        bucket = s3.Bucket(bucket_name)

        # Build filename
        file_name = StringHelper.generate_uuid() + "." + ResourceZipper.COMPRESS_EXTENSION
        prefix = params.get_value('s3_object_prefix')
        if prefix is not None:
            # check if the prefix ends with a slash
            if prefix[-1] == "/":
                file_name = prefix + file_name
            else:
                file_name = prefix + "/" + file_name

        mime_type = FileHelper.get_mime(self.zip_file_path)
        total_size = FileHelper.get_size(self.zip_file_path)

        self.transfered_bytes = 0
        self.last_progress = 0
        start_time = time.time()

        self.log_info_message(f"Uploading resource to S3 bucket '{bucket_name}'")

        with open(self.zip_file_path, 'rb') as data:
            bucket.upload_fileobj(data, file_name,
                                  ExtraArgs={
                                      'ContentType': mime_type,
                                  }, Callback=lambda progress: self.progress_callback(progress, total_size, start_time))

        duration = DateHelper.get_duration_pretty_text(
            time.time() - start_time)
        self.log_success_message(
            f"Uploaded resource to bucket '{bucket_name}' in {duration}")

        if params.get_value('send_me_an_email'):
            self.send_email(bucket_name, file_name)
        return {}

    def progress_callback(self, transfered_bytes: int, total_size: int, start_time: float) -> None:
        self.transfered_bytes += transfered_bytes
        progress = int(self.transfered_bytes / total_size * 100)

        # log progress every 3%
        if progress - self.last_progress > 3:
            self.last_progress = progress
            transfered_str = FileHelper.get_file_size_pretty_text(self.transfered_bytes)
            total_str = FileHelper.get_file_size_pretty_text(total_size)
            # calculate remaining time
            remaining_time = (
                time.time() - start_time) / (self.transfered_bytes / total_size) - (time.time() - start_time)

            remaining_time_str = DateHelper.get_duration_pretty_text(
                remaining_time)

            self.update_progress_value(
                progress, f"Uploaded {transfered_str}/{total_str} ({progress}%) - {remaining_time_str} remaining")

    def send_email(self, bucket_name: str, file_name: str) -> None:
        self.log_info_message("Sending email")
        MailService.send_mail_to_current_user(f"""
<p>Hello,</p>

<p>Your resource has been successfully uploaded to S3 bucket '{bucket_name}'.</p>

<p>It was zipped into the following file: <strong>{file_name}</strong></p>""", "Resource uploaded to S3")

    def run_after_task(self) -> None:
        if self.zip_file_path is not None:
            FileHelper.delete_file(self.zip_file_path)

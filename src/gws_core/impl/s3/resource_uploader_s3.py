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
from gws_core.impl.s3.s3_bucket import S3Bucket
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


@task_decorator(unique_name="ResourceUploaderS3", human_name="Upload resource to S3",
                short_description="Simple task to send the input resource to a S3 bucket")
class ResourceUploaderS3(Task):
    input_specs: InputSpecs = {'resource': InputSpec(Resource)}
    output_specs: OutputSpecs = {}
    config_specs: ConfigSpecs = {
        's3_endpoint': StrParam(human_name="S3 endpoint"),
        's3_region': StrParam(human_name="S3 region"),
        's3_access_key_id': StrParam(human_name="S3 access key id"),
        's3_secret_access_key': StrParam(human_name="S3 secret access key"),
        's3_bucket': StrParam(human_name="S3 bucket name"),
        's3_object_prefix': StrParam(human_name="Prefix for the S3 object", default_value=""),
        'send_me_an_email': BoolParam(human_name="Send me an email when the task is finished", default_value=False)
    }

    zip_file_path: str = None

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        bucket_name = params.get_value('s3_bucket')

        self.log_info_message('Zipping resource')
        resource: Resource = inputs['resource']
        resource_zipper = ResourceZipper(CurrentUserService.get_current_user())
        resource_zipper.add_resource(resource)
        self.zip_file_path = resource_zipper.close_zip()

        s3_bucket = S3Bucket(endpoint=params.get_value('s3_endpoint'),
                             region=params.get_value('s3_region'),
                             access_key_id=params.get_value('s3_access_key_id'),
                             secret_access_key=params.get_value('s3_secret_access_key'),
                             bucket_name=bucket_name,
                             message_dispatcher=self.message_dispatcher)

        # Build filename
        file_name = StringHelper.generate_uuid() + "." + ResourceZipper.COMPRESS_EXTENSION

        # add prefix
        prefix = params.get_value('s3_object_prefix')
        if prefix:
            # if prefix does not end with a slash, add it
            if not prefix.endswith('/'):
                prefix += '/'
            file_name = prefix + file_name

        # upload file
        s3_bucket.upload_file(self.zip_file_path, file_name)

        if params.get_value('send_me_an_email'):
            self.send_email(bucket_name, file_name)
        return {}

    def send_email(self, bucket_name: str, file_name: str) -> None:
        self.log_info_message("Sending email")
        MailService.send_mail_to_current_user(f"""
<p>Hello,</p>

<p>Your resource has been successfully uploaded to S3 bucket '{bucket_name}'.</p>

<p>It was zipped into the following file: <strong>{file_name}</strong></p>""", "Resource uploaded to S3")

    def run_after_task(self) -> None:
        if self.zip_file_path is not None:
            FileHelper.delete_file(self.zip_file_path)

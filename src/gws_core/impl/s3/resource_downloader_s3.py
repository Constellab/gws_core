# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core.config.param.param_spec import StrParam
from gws_core.impl.s3.s3_bucket import S3Bucket
from gws_core.share.resource_downloader_base import ResourceDownloaderBase

from ...config.config_types import ConfigParams, ConfigSpecs
from ...task.task_decorator import task_decorator
from ...task.task_io import TaskInputs, TaskOutputs


@task_decorator(unique_name="ResourceDownloaderS3", human_name="Download resource from a S3 bucket")
class ResourceDownloaderS3(ResourceDownloaderBase):
    """
    Task to download a resource from an external source using an HTTP link.

    If the link is from a Gencovery lab, the resource downloaded and imported in the correct type.
    Then it will be marked as received in the origin lab.

    If the link refers to a zip file, the zip file will be unzipped and the resource will be imported (File or Folder).

    If the link refers to a file, the file will be imported as a resource.

    """

    config_specs: ConfigSpecs = {
        's3_endpoint': StrParam(human_name="S3 endpoint"),
        's3_region': StrParam(human_name="S3 region"),
        's3_access_key_id': StrParam(human_name="S3 access key id"),
        's3_secret_access_key': StrParam(human_name="S3 secret access key"),
        's3_bucket': StrParam(human_name="S3 bucket name"),
        'object_key': StrParam(human_name="Key of the S3 object in bucket"),
    }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        s3_bucket = S3Bucket(endpoint=params.get_value('s3_endpoint'),
                             region=params.get_value('s3_region'),
                             access_key_id=params.get_value('s3_access_key_id'),
                             secret_access_key=params.get_value('s3_secret_access_key'),
                             bucket_name=params.get_value('s3_bucket'),
                             message_dispatcher=self.message_dispatcher)

        # download the file
        resource_file = s3_bucket.get_object(params.get_value('object_key'))

        return self.create_resource_from_file(resource_file)

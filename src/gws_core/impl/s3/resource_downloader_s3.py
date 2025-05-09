

from gws_core.config.param.param_spec import StrParam
from gws_core.credentials.credentials_param import CredentialsParam
from gws_core.credentials.credentials_type import (CredentialsDataS3,
                                                   CredentialsType)
from gws_core.impl.s3.s3_bucket import S3Bucket
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.task.resource_downloader_base import \
    ResourceDownloaderBase
from gws_core.share.shared_dto import ShareEntityCreateMode

from ...config.config_params import ConfigParams
from ...config.config_specs import ConfigSpecs
from ...task.task_decorator import task_decorator
from ...task.task_io import TaskInputs, TaskOutputs


@task_decorator(unique_name="ResourceDownloaderS3", human_name="Download resource from a S3 bucket",
                style=TypingStyle.material_icon("cloud_download"))
class ResourceDownloaderS3(ResourceDownloaderBase):
    """
    Task to download a resource from an S3 bucket.

    If the downloaded file is a zipped Resource, the resource will be unzipped and imported in the original format.

    If the link refers to a normal zip file, the zip file will be unzipped and the resource will be imported (File or Folder).
    See the uncompress parameter.

    If the link refers to a file, the file will be imported as a resource.

    See ResourceUploaderS3 to upload a resource to an S3 bucket.
    """

    config_specs = ConfigSpecs({
        'credentials': CredentialsParam(credentials_type=CredentialsType.S3),
        'object_key': StrParam(human_name="Key of the S3 object in bucket"),
        's3_bucket': StrParam(human_name="S3 bucket name",
                              short_description="If provided, override the bucket name in credentials",
                              optional=True),
        'uncompress': ResourceDownloaderBase.uncompressConfig
    })

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        credentials: CredentialsDataS3 = params.get_value('credentials')

        bucket_name = credentials.bucket or params.get_value('s3_bucket')
        if not bucket_name:
            raise ValueError("Bucket name is not provided")

        s3_bucket = S3Bucket(endpoint=credentials.endpoint_url,
                             region=credentials.region,
                             access_key_id=credentials.access_key_id,
                             secret_access_key=credentials.secret_access_key,
                             bucket_name=bucket_name,
                             message_dispatcher=self.message_dispatcher)

        # download the file
        resource_file = s3_bucket.get_object(params.get_value('object_key'))

        resource = self.create_resource_from_file(resource_file, params['uncompress'],
                                                  ShareEntityCreateMode.NEW_ID)
        return {'resource': resource}

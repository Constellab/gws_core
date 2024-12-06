

from datetime import timedelta

from gws_core.config.config_params import ConfigParams
from gws_core.config.config_types import ConfigSpecs
from gws_core.config.param.param_spec import IntParam
from gws_core.core.utils.date_helper import DateHelper
from gws_core.credentials.credentials_param import CredentialsParam
from gws_core.credentials.credentials_type import (CredentialsDataLab,
                                                   CredentialsType)
from gws_core.external_lab.external_lab_api_service import \
    ExternalLabApiService
from gws_core.external_lab.external_lab_dto import ExternalLabImportRequestDTO
from gws_core.io.io_spec import InputSpec
from gws_core.io.io_specs import InputSpecs
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.resource import Resource
from gws_core.resource.task.resource_downloader_http import \
    ResourceDownloaderHttp
from gws_core.share.share_link_service import ShareLinkService
from gws_core.share.shared_dto import GenerateShareLinkDTO, ShareLinkType
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs
from gws_core.user.current_user_service import CurrentUserService


@task_decorator(unique_name="SendResourceToLab", human_name="Send the resource to a lab",
                short_description="Send a resource to another lab using a share link",
                style=TypingStyle.material_icon("cloud_upload"))
class SendResourceToLab(Task):
    """
    Task to send a resource to another lab using a share link.

    This task creates a share link for the resource.

    Then it call the external lab API to import the resource in the external lab using the share link.

    A credentials of type lab are required in both labs to be able to send and receive resources. It
    needs to be the same api_key in both labs.

    """

    input_specs = InputSpecs({
        'resource': InputSpec(Resource, human_name="Resource to send"),
    })

    config_specs: ConfigSpecs = {
        'credentials': CredentialsParam(credentials_type=CredentialsType.LAB, human_name="Lab credentials",
                                        short_description="The credentials must exist in destination lab"),
        'link_duration': IntParam(human_name='Share link duration in days',
                                  short_description="The share link is not created if a share link already exists for the resource",
                                  min_value=1,
                                  max_value=365, default_value=1),
    }

    INPUT_NAME = 'resource'

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        resource: Resource = inputs.get('resource')

        current_day = DateHelper.now_utc()

        generate_share_link = GenerateShareLinkDTO(
            entity_id=resource.get_model_id(),
            entity_type=ShareLinkType.RESOURCE,
            valid_until=current_day + timedelta(days=params.get_value('link_duration'))
        )

        self.log_info_message(f"Generate share link for resource {resource.get_model_id()} if not exists")
        share_link = ShareLinkService.get_or_create_valid_share_link(generate_share_link)

        # Call the external lab API to import the resource
        self.log_info_message("Send the resource to the lab")
        request_dto = ExternalLabImportRequestDTO(
            # convert to ResourceDownloaderHttp config because ResourceDownloaderHttp is used to download the resource
            params=ResourceDownloaderHttp.build_config(
                link=share_link.get_download_link(),
                uncompress='yes', create_option='Skip if exists')
        )
        credentials: CredentialsDataLab = params.get_value('credentials')

        response = ExternalLabApiService.send_resource_to_lab(request_dto, credentials,
                                                              CurrentUserService.get_and_check_current_user().id)

        self.log_success_message(f"Resource sent to the lab, available at {response.resource_url}")

        return {}

from datetime import timedelta

from gws_core.config.config_params import ConfigParams, ConfigParamsDict
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import IntParam
from gws_core.core.utils.date_helper import DateHelper
from gws_core.credentials.credentials_param import CredentialsParam
from gws_core.credentials.credentials_type import CredentialsDataLab, CredentialsType
from gws_core.external_lab.external_lab_api_service import ExternalLabApiService
from gws_core.external_lab.external_lab_dto import ExternalLabImportRequestDTO
from gws_core.io.io_spec import InputSpec
from gws_core.io.io_specs import InputSpecs
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.resource import Resource
from gws_core.resource.task.resource_downloader_http import (
    ResourceDownloaderCreateOption,
    ResourceDownloaderHttp,
)
from gws_core.scenario.scenario_enums import ScenarioStatus
from gws_core.scenario.scenario_waiter import ScenarioWaiterExternalLab
from gws_core.share.share_link_service import ShareLinkService
from gws_core.share.shared_dto import GenerateShareLinkDTO, ShareLinkEntityType
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs
from gws_core.user.current_user_service import CurrentUserService


@task_decorator(
    unique_name="SendResourceToLab",
    human_name="Send the resource to a lab",
    short_description="Send a resource to another lab using a share link",
    style=TypingStyle.material_icon("cloud_upload"),
)
class SendResourceToLab(Task):
    """
    Task to send a resource to another lab using a share link.

    This task creates a share link for the resource. A import scenario is created in the destination lab.

    Then it call the external lab API to import the resource in the external lab using the share link.

    A credentials of type lab are required in both labs to be able to send and receive resources. It
    needs to be the same api_key in both labs.

    Check the following documentation to see how to configure the lab credentials:
    https://constellab.community/bricks/gws_academy/latest/doc/data-lab/resource/51b1f255-e08f-41f6-b503-10e37ea277b0#send-resources-to-another-lab-(e.g.-a-datahub)
    """

    input_specs = InputSpecs(
        {
            "resource": InputSpec(Resource, human_name="Resource to send"),
        }
    )

    config_specs = ConfigSpecs(
        {
            "credentials": CredentialsParam(
                credentials_type=CredentialsType.LAB,
                human_name="Lab credentials",
                short_description="The credentials must exist in destination lab",
            ),
            "link_duration": IntParam(
                human_name="Share link duration in days",
                short_description="The share link is not created if a share link already exists for the resource",
                min_value=1,
                max_value=365,
                default_value=1,
            ),
            "create_option": ResourceDownloaderHttp.config_specs.get_spec("create_option"),
        }
    )

    INPUT_NAME = "resource"

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        resource: Resource = inputs.get("resource")

        current_day = DateHelper.now_utc()

        generate_share_link = GenerateShareLinkDTO(
            entity_id=resource.get_model_id(),
            entity_type=ShareLinkEntityType.RESOURCE,
            valid_until=current_day + timedelta(days=params.get_value("link_duration")),
        )

        self.log_info_message(
            f"Generate share link for resource {resource.get_model_id()} if not exists"
        )
        share_link = ShareLinkService.get_or_create_valid_public_share_link(generate_share_link)

        # Call the external lab API to import the resource
        credentials: CredentialsDataLab = params.get_value("credentials")
        self.log_info_message(
            f"Send the resource to the lab {ExternalLabApiService.get_full_route(credentials, '')}"
        )
        request_dto = ExternalLabImportRequestDTO(
            # convert to ResourceDownloaderHttp config because ResourceDownloaderHttp is used to download the resource
            params=ResourceDownloaderHttp.build_config(
                link=share_link.get_download_link(),
                uncompress="yes",
                create_option=params["create_option"],
            )
        )

        response = ExternalLabApiService.send_resource_to_lab(
            request_dto, credentials, CurrentUserService.get_and_check_current_user().id
        )

        self.log_success_message(
            f"Import of resource started, follow progress in destination lab : {response.scenario_url}"
        )

        scenario_waiter = ScenarioWaiterExternalLab(
            response.scenario.id, credentials, CurrentUserService.get_and_check_current_user().id
        )

        # refresh every 30 seconds, max 2 hours
        scenario_info = scenario_waiter.wait_until_finished(
            refresh_interval=30,
            refresh_interval_max_count=240,
            message_dispatcher=self.message_dispatcher,
        )

        if scenario_info.scenario.status != ScenarioStatus.SUCCESS:
            error = (
                scenario_info.progress.last_message.text
                if scenario_info.progress and scenario_info.progress.has_last_message()
                else "Unknown error"
            )
            raise Exception(
                f"Export resource to lab failed, status: {scenario_info.scenario.status}. Error details: {error}"
            )

        self.log_success_message("Resource imported in the lab, retrieve resource info")

        resource_info = ExternalLabApiService.get_imported_resource_from_scenario(
            response.scenario.id, credentials, CurrentUserService.get_and_check_current_user().id
        )

        self.log_success_message(f"Imported resource url: {resource_info.resource_url}")

        return {}

    @classmethod
    def build_config(
        cls,
        credentials: CredentialsDataLab | str,
        link_duration: int,
        create_option: ResourceDownloaderCreateOption,
    ) -> ConfigParamsDict:
        return ConfigParams(
            {
                "credentials": credentials,
                "link_duration": link_duration,
                "create_option": create_option,
            }
        )

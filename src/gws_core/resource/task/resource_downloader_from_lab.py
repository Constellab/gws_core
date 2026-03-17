from gws_core.config.config_params import ConfigParams
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.external_lab.external_lab_api_service import ExternalLabApiService
from gws_core.lab.lab_model.lab_dto import LabDTOWithCredentials
from gws_core.lab.lab_model.lab_model_param import LabModelParam
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.resource_downloader import LabShareZipRouteDownloader
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.task.resource_downloader_base import ResourceDownloaderBase
from gws_core.share.shared_dto import ShareEntityCreateMode
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs
from gws_core.user.current_user_service import CurrentUserService


@task_decorator(
    unique_name="ResourceDownloaderFromLab",
    human_name="Download resource from a lab",
    short_description="Download a resource from another lab using lab credentials",
    style=TypingStyle.material_icon("cloud_download"),
)
class ResourceDownloaderFromLab(ResourceDownloaderBase):
    """
    Task to download a resource from another lab using lab credentials.

    Unlike ResourceDownloaderHttp which uses share links, this task authenticates
    directly with the external lab via credentials to download a specific resource.
    """

    config_specs: ConfigSpecs = ConfigSpecs(
        {
            "lab": LabModelParam(
                human_name="Source lab",
                short_description="The lab to download the resource from (must have credentials configured)",
            ),
            "resource_id": StrParam(
                human_name="Resource ID",
                short_description="ID of the resource to download on the source lab",
            ),
            "uncompress": ResourceDownloaderBase.uncompress_config,
            "skip_tags": ResourceDownloaderBase.skip_tags_config,
        }
    )

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        lab_dto: LabDTOWithCredentials = params.get_value("lab")
        resource_id: str = params.get_value("resource_id")
        user_id = CurrentUserService.get_and_check_current_user().id

        external_lab_service = ExternalLabApiService(lab_dto, user_id)

        # Build the zip route URL for the resource on the external lab
        zip_url = external_lab_service.get_resource_zip_route(resource_id)
        auth_headers = external_lab_service._get_auth_headers()

        # Download the resource zip using credential-based auth
        self.log_info_message("Downloading resource from external lab")
        downloader = LabShareZipRouteDownloader(
            zip_url, self.message_dispatcher, headers=auth_headers
        )
        resource_file = downloader.download()

        # Create the resource from the downloaded file
        resource = self.create_resource_from_file(
            resource_file,
            params.get_value("uncompress"),
            ShareEntityCreateMode.KEEP_ID,
            ResourceOrigin.IMPORTED_FROM_LAB,
            skip_tags=params.get_value("skip_tags"),
        )

        return {"resource": resource}

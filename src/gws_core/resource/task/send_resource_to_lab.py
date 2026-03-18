from gws_core.config.config_params import ConfigParams, ConfigParamsDict
from gws_core.config.config_specs import ConfigSpecs
from gws_core.external_lab.external_lab_api_service import ExternalLabApiService
from gws_core.external_lab.external_lab_dto import ExternalLabImportRequestDTO
from gws_core.io.io_spec import InputSpec
from gws_core.io.io_specs import InputSpecs
from gws_core.lab.lab_model.lab_dto import LabDTOWithCredentials
from gws_core.lab.lab_model.lab_model_param import LabModelParam
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.resource import Resource
from gws_core.resource.task.resource_downloader_from_lab import ResourceDownloaderFromLab
from gws_core.scenario.scenario_enums import ScenarioStatus
from gws_core.scenario.scenario_waiter import ScenarioWaiterExternalLab
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs
from gws_core.user.current_user_service import CurrentUserService


@task_decorator(
    unique_name="SendResourceToLab",
    human_name="Send the resource to a lab",
    short_description="Send a resource to another lab using lab credentials",
    style=TypingStyle.material_icon("cloud_upload"),
)
class SendResourceToLab(Task):
    """
    Task to send a resource to another lab using lab credentials.

    This task instructs the destination lab to import the resource from the source lab
    using credential-based authentication.

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
            "lab": LabModelParam(
                human_name="Destination lab",
                short_description="The lab to send the resource to (must have credentials configured)",
            ),
            "uncompress": ResourceDownloaderFromLab.config_specs.get_spec("uncompress"),
            "create_option": ResourceDownloaderFromLab.config_specs.get_spec("create_option"),
            "skip_tags": ResourceDownloaderFromLab.config_specs.get_spec("skip_tags"),
        }
    )

    INPUT_NAME = "resource"

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        resource: Resource = inputs.get("resource")

        # Call the external lab API to import the resource
        lab_dto: LabDTOWithCredentials = params.get_value("lab")
        external_lab_service = ExternalLabApiService(lab_dto, CurrentUserService.get_and_check_current_user().id)
        self.log_info_message(
            f"Send the resource to the lab {external_lab_service.get_full_route('')}"
        )

        # The destination lab resolves the source lab's LabModel from the
        # auth context (set during API key authentication), so we don't
        # need to pass the lab id in the params.
        request_dto = ExternalLabImportRequestDTO(
            params=ResourceDownloaderFromLab.build_config(
                resource_id=resource.get_model_id(),
                uncompress=params["uncompress"],
                create_option=params["create_option"],
                skip_tags=params["skip_tags"],
            )
        )

        response = external_lab_service.send_resource_to_lab(request_dto)

        self.log_success_message(
            f"Import of resource started, follow progress in destination lab : {response.scenario_url}"
        )

        scenario_waiter = ScenarioWaiterExternalLab(external_lab_service, response.scenario.id)

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

        resource_info = external_lab_service.get_imported_resource_from_scenario(
            response.scenario.id
        )

        self.log_success_message(f"Imported resource url: {resource_info.resource_url}")

        return {}

    @classmethod
    def build_config(
        cls,
        lab: LabDTOWithCredentials | str,
        uncompress: str = "auto",
        create_option: str = "Update if exists",
        skip_tags: bool = False,
    ) -> ConfigParamsDict:
        return {
            "lab": lab,
            "uncompress": uncompress,
            "create_option": create_option,
            "skip_tags": skip_tags,
        }

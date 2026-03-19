from gws_core.config.config_params import ConfigParams, ConfigParamsDict
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import BoolParam
from gws_core.external_lab.external_lab_api_service import ExternalLabApiService
from gws_core.external_lab.external_lab_dto import ExternalLabImportRequestDTO
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.lab.lab_model.lab_dto import LabDTOWithCredentials
from gws_core.lab.lab_model.lab_model_param import LabModelParam
from gws_core.model.typing_style import TypingStyle
from gws_core.scenario.scenario_enums import ScenarioStatus
from gws_core.scenario.scenario_waiter import ScenarioWaiterExternalLab
from gws_core.scenario.task.scenario_downloader_base import (
    ScenarioDownloaderCreateOption,
    ScenarioDownloaderResourceMode,
)
from gws_core.scenario.task.scenario_downloader_from_lab import ScenarioDownloaderFromLab
from gws_core.scenario.task.scenario_resource import ScenarioResource
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs
from gws_core.user.current_user_service import CurrentUserService


@task_decorator(
    unique_name="SendScenarioToLab",
    human_name="Send a scenario to a lab",
    short_description="Send a scenario to another lab using lab credentials",
    style=TypingStyle.material_icon("cloud_upload"),
)
class SendScenarioToLab(Task):
    """
    Task to send a scenario to another lab using lab credentials.

    This task instructs the destination lab to import the scenario from the source lab
    using credential-based authentication.

    A credentials of type lab are required in both labs to be able to send and receive scenarios. It
    needs to be the same api_key in both labs.

    When `auto_run` is enabled, the create_option is forced to "Update if exists" so the
    scenario keeps the same ID. The auto_run flag is passed to the destination's downloader
    which will automatically run the scenario after import. The task does NOT unmark the
    scenario — downstream tasks (WaitExternalScenario) handle unmarking.

    The following documentation explain how to configure the lab credentials:
    https://constellab.community/bricks/gws_academy/latest/doc/data-lab/scenario/f4453296-ccc5-4b54-8e46-2d1c2f830a0c#send-a-scenario-to-another-lab-(e.g.-a-datahub)
    """

    input_specs = InputSpecs(
        {
            "scenario": InputSpec(
                ScenarioResource,
                human_name="Scenario to send",
                short_description="Scenario to send, it must not be running",
            ),
        }
    )

    output_specs = OutputSpecs({"scenario": OutputSpec(ScenarioResource, human_name="Scenario")})

    config_specs = ConfigSpecs(
        {
            "lab": LabModelParam(
                human_name="Destination lab",
                short_description="The lab to send the scenario to (must have credentials configured)",
            ),
            "resource_mode": ScenarioDownloaderFromLab.config_specs.get_spec("resource_mode"),
            "create_option": ScenarioDownloaderFromLab.config_specs.get_spec("create_option"),
            "auto_run": BoolParam(
                default_value=False,
                human_name="Auto run in destination lab",
                short_description="If true, the scenario will be automatically run in the destination lab",
            ),
        }
    )

    INPUT_NAME = "scenario"
    OUTPUT_NAME = "scenario"

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        scenario_resource: ScenarioResource = inputs["scenario"]

        scenario = scenario_resource.get_scenario()

        if scenario.is_running:
            raise ValueError("The scenario is running, it cannot be sent to the lab")
        if scenario.is_running_in_external_lab:
            raise ValueError("The scenario is already running in an external lab")

        auto_run: bool = params.get_value("auto_run")
        lab_dto: LabDTOWithCredentials = params.get_value("lab")
        create_option = params["create_option"]

        # When auto_run is enabled, force "Update if exists" so scenario keeps same ID
        if auto_run:
            create_option = "Update if exists"

        external_lab_service = ExternalLabApiService(
            lab_dto, CurrentUserService.get_and_check_current_user().id
        )
        self.log_info_message(
            f"Send the scenario to the lab {external_lab_service.get_full_route('')}"
        )

        # The destination lab resolves the source lab's LabModel from the
        # auth context (set during API key authentication), so we don't
        # need to pass the lab id in the params.
        request_dto = ExternalLabImportRequestDTO(
            params=ScenarioDownloaderFromLab.build_config(
                scenario_id=scenario_resource.scenario_id,
                resource_mode=params["resource_mode"],
                create_option=create_option,
                auto_run=auto_run,
            ),
        )

        if auto_run:
            # Lock the scenario while it's being processed externally
            scenario.mark_as_running_in_external_lab()

        try:
            response = external_lab_service.send_scenario_to_lab(request_dto)

            self.log_success_message(
                f"Import of scenario started, follow progress in destination lab : {response.scenario_url}"
            )

            # This waits for the import scenario to finish
            import_scenario_waiter = ScenarioWaiterExternalLab(
                external_lab_service, response.scenario.id
            )

            # refresh every 30 seconds, max 2 hours
            import_scenario_info = import_scenario_waiter.wait_until_finished(
                refresh_interval=30,
                refresh_interval_max_count=240,
                message_dispatcher=self.message_dispatcher,
            )

            if import_scenario_info.scenario.status != ScenarioStatus.SUCCESS:
                error = (
                    import_scenario_info.progress.last_message.text
                    if import_scenario_info.progress
                    and import_scenario_info.progress.has_last_message()
                    else "Unknown error"
                )
                raise Exception(
                    f"Export scenario to lab failed, status: {import_scenario_info.scenario.status}. Error details: {error}"
                )

            return {"scenario": scenario_resource}
        except Exception as err:
            if auto_run:
                # When auto_run, only unmark as running if there is an error
                # the next task (WaitExternalScenario) is responsible for unmarking when the scenario finishes running in the external lab
                scenario = scenario.refresh()
                scenario.unmark_running_in_external_lab()
            raise err

    @classmethod
    def build_config(
        cls,
        lab: str,
        resource_mode: ScenarioDownloaderResourceMode,
        create_option: ScenarioDownloaderCreateOption,
        auto_run: bool = False,
    ) -> ConfigParamsDict:
        return {
            "lab": lab,
            "resource_mode": resource_mode,
            "create_option": create_option,
            "auto_run": auto_run,
        }

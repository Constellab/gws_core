from gws_core.config.config_params import ConfigParams, ConfigParamsDict
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.external_lab.external_lab_api_service import ExternalLabApiService
from gws_core.io.io_spec import InputSpec
from gws_core.io.io_specs import InputSpecs
from gws_core.lab.lab_model.lab_dto import LabDTOWithCredentials
from gws_core.lab.lab_model.lab_model_param import LabModelParam
from gws_core.model.typing_style import TypingStyle
from gws_core.scenario.task.scenario_downloader_base import ScenarioDownloaderBase
from gws_core.scenario.task.scenario_resource import ScenarioResource
from gws_core.share.shared_dto import ShareScenarioInfoReponseDTO
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs
from gws_core.user.current_user_service import CurrentUserService


@task_decorator(
    unique_name="ScenarioDownloaderFromLab",
    human_name="Download a scenario from a lab",
    short_description="Download a scenario from another lab using lab credentials",
    style=TypingStyle.material_icon("scenario"),
)
class ScenarioDownloaderFromLab(ScenarioDownloaderBase):
    """
    Download a scenario from another lab using lab credentials.

    This task retrieves a scenario (its protocol structure, tasks, and optionally its resources)
    from an external lab by authenticating with pre-configured lab credentials, without requiring
    a share link.

    The scenario to download is identified by its ID, which can be provided in two ways:
    - Via the **source_scenario** input: useful when the current lab previously sent a scenario
      to the external lab and wants to download the results back.
    - Via the **scenario_id** config parameter: useful when pulling a scenario directly
      from the external lab by its known ID.

    ## Inputs

    - **source_scenario** *(optional)*: A `ScenarioResource` referencing the scenario to download.
      When provided, its scenario ID is used and the `scenario_id` config parameter is ignored.

    ## Parameters

    - **lab**: The external lab to connect to. Must have credentials configured in the current lab.
    - **scenario_id** *(optional)*: The ID of the scenario to download. Required when no input is provided.
    - **resource_mode**: Controls which resources are downloaded along with the scenario:
      - `Auto`: Automatically selects the best mode based on the scenario status
        (e.g. inputs for draft scenarios, outputs for finished ones, inputs of draft tasks for partially run scenarios).
      - `Inputs and outputs`: Downloads both input and output resources.
      - `Inputs only`: Downloads only the input resources.
      - `Outputs only`: Downloads only the output resources.
      - `All`: Downloads all resources (inputs, outputs, and intermediate results).
      - `Inputs of draft tasks`: Downloads only the input resources of tasks that have not been run yet (DRAFT status).
        Useful for partially run scenarios where only the remaining tasks need their inputs.
      - `None`: Downloads only the scenario structure without any resource content.
    - **create_option**: Determines how to handle an existing scenario with the same ID:
      - `Update if exists`: Updates the existing scenario in place.
      - `Skip if exists`: Raises an error if the scenario already exists.
      - `Force new scenario`: Creates a new scenario with a new ID, even if one already exists.
    - **auto_run**: If enabled, the scenario is automatically queued for execution after download.
      Requires the resource mode to include input resources.
    - **skip_scenario_tags**: If enabled, scenario-level tags from the source are not applied.
    - **skip_resource_tags**: If enabled, resource-level tags from the source are not applied.

    ## Output

    - **scenario**: A `ScenarioResource` referencing the downloaded scenario.
    """

    input_specs = InputSpecs(
        {
            "source_scenario": InputSpec(
                ScenarioResource,
                human_name="Source scenario",
                short_description="The scenario that was sent to the external lab",
                optional=True,
            ),
        }
    )

    config_specs = ConfigSpecs(
        {
            "lab": LabModelParam(
                human_name="Source lab",
                short_description="The lab to download the scenario from (must have credentials configured)",
            ),
            "scenario_id": StrParam(
                human_name="Scenario ID",
                short_description="ID of the scenario to download (used when no input is provided)",
                optional=True,
                default_value="",
            ),
            **ScenarioDownloaderBase.config_specs.specs,
        }
    )

    INPUT_NAME = "source_scenario"

    _external_lab_service: ExternalLabApiService
    _scenario_id: str

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        lab_dto: LabDTOWithCredentials = params.get_value("lab")
        user_id = CurrentUserService.get_and_check_current_user().id
        self._external_lab_service = ExternalLabApiService(lab_dto, user_id)

        # Get scenario_id from input or config
        scenario_resource: ScenarioResource | None = inputs.get(self.INPUT_NAME)
        if scenario_resource is not None:
            self._scenario_id = scenario_resource.scenario_id
        else:
            self._scenario_id = params.get_value("scenario_id")
            if not self._scenario_id:
                raise Exception("scenario_id must be provided either via input or config")

        self.share_entity = self._get_scenario_info()

        scenario = self._build_and_download_scenario(params, self.share_entity)

        return {"scenario": ScenarioResource(scenario.id)}

    def _get_scenario_info(self) -> ShareScenarioInfoReponseDTO:
        """Fetch scenario metadata from the external lab using credentials."""
        self.log_info_message("Fetching scenario export info from external lab using credentials")
        return self._external_lab_service.get_scenario_export_info(self._scenario_id)

    def _get_request_headers(self) -> dict | None:
        """Return auth headers for credential-based requests."""
        return self._external_lab_service._get_auth_headers()

    @classmethod
    def build_config(
        cls,
        lab: str | None = None,
        scenario_id: str | None = None,
        resource_mode: str = "Outputs only",
        create_option: str = "Update if exists",
        auto_run: bool = False,
        skip_scenario_tags: bool = False,
        skip_resource_tags: bool = False,
    ) -> ConfigParamsDict:
        return {
            "scenario_id": scenario_id,
            "resource_mode": resource_mode,
            "create_option": create_option,
            "auto_run": auto_run,
            "lab": lab,
            "skip_scenario_tags": skip_scenario_tags,
            "skip_resource_tags": skip_resource_tags,
        }

from gws_core.config.config_params import ConfigParams, ConfigParamsDict
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.credentials.credentials_param import CredentialsParam
from gws_core.credentials.credentials_type import CredentialsDataLab, CredentialsType
from gws_core.external_lab.external_lab_api_service import ExternalLabApiService
from gws_core.io.io_spec import InputSpec
from gws_core.io.io_specs import InputSpecs
from gws_core.model.typing_style import TypingStyle
from gws_core.scenario.task.scenario_downloader import BaseScenarioDownloader
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
class ScenarioDownloaderFromLab(BaseScenarioDownloader):
    """
    Task to download a scenario from another lab using lab credentials.

    Unlike ScenarioDownloader which uses share links, this task authenticates
    directly with the external lab via credentials.

    The scenario_id can come from either:
    - An input ScenarioResource (when used in the source lab's export pipeline
      to download outputs back from the destination)
    - A config parameter `scenario_id` (when used in the destination lab's
      import flow to pull the scenario from the source)
    """

    input_specs = InputSpecs(
        {
            "source_scenario": InputSpec(
                ScenarioResource,
                human_name="Source scenario",
                short_description="The scenario that was sent to the external lab",
                is_optional=True,
            ),
        }
    )

    config_specs = ConfigSpecs(
        {
            "credentials": CredentialsParam(
                credentials_type=CredentialsType.LAB,
                human_name="Lab credentials",
                short_description="Credentials of the external lab to download from",
            ),
            "scenario_id": StrParam(
                human_name="Scenario ID",
                short_description="ID of the scenario to download (used when no input is provided)",
                optional=True,
                default_value="",
            ),
            **BaseScenarioDownloader.config_specs.specs,
        }
    )

    INPUT_NAME = "source_scenario"

    _credentials: CredentialsDataLab
    _user_id: str
    _scenario_id: str

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        self._credentials = params.get_value("credentials")
        self._user_id = CurrentUserService.get_and_check_current_user().id

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
        return ExternalLabApiService.get_scenario_export_info(
            self._scenario_id, self._credentials, self._user_id
        )

    def _get_request_headers(self) -> dict | None:
        """Return auth headers for credential-based requests."""
        return ExternalLabApiService._get_external_lab_auth(
            self._credentials.api_key, self._user_id
        )

    @classmethod
    def build_config(
        cls,
        credentials: str,
        scenario_id: str = "",
        resource_mode: str = "Outputs only",
        create_option: str = "Update if exists",
        auto_run: bool = False,
    ) -> ConfigParamsDict:
        return {
            "credentials": credentials,
            "scenario_id": scenario_id,
            "resource_mode": resource_mode,
            "create_option": create_option,
            "auto_run": auto_run,
        }

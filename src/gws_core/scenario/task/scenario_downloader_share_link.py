import requests

from gws_core.config.config_params import ConfigParams, ConfigParamsDict
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.external_lab.external_lab_api_service import ExternalLabApiService
from gws_core.model.typing_style import TypingStyle
from gws_core.scenario.task.scenario_downloader_base import (
    ScenarioDownloaderBase,
    ScenarioDownloaderCreateOption,
    ScenarioDownloaderResourceMode,
)
from gws_core.scenario.task.scenario_resource import ScenarioResource
from gws_core.share.share_link import ShareLink
from gws_core.share.shared_dto import (
    ShareLinkEntityType,
    ShareScenarioInfoReponseDTO,
)
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs
from gws_core.user.current_user_service import CurrentUserService


@task_decorator(
    unique_name="ScenarioDownloaderShareLink",
    human_name="Download a scenario",
    short_description="Download a scenario from another lab using a share link",
    style=TypingStyle.material_icon("scenario"),
)
class ScenarioDownloaderShareLink(ScenarioDownloaderBase):
    """
    Download a scenario from another lab using a share link.

    This task retrieves a scenario (its protocol structure, tasks, and optionally its resources)
    from another lab using a public or space-scoped share link. It is commonly used to transfer
    scenarios between a development and a production environment.

    After a successful download, the task notifies the origin lab that the scenario has been received.

    ## Parameters

    - **link**: The share link URL of the scenario to download. Must be a valid lab share scenario link.
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

    config_specs = ConfigSpecs(
        {
            "link": StrParam(
                human_name="Scenario link", short_description="Link to download the scenario"
            ),
            **ScenarioDownloaderBase.config_specs.get_specs_as_dict(),
        }
    )

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        link = params["link"]

        if not ShareLink.is_lab_share_scenario_link(link):
            raise Exception(
                "Invalid link, are you sure this a link of a share scenario from a lab ?"
            )

        self._link = link
        self.share_entity = self._get_scenario_info()

        scenario = self._build_and_download_scenario(params, self.share_entity)

        return {"scenario": ScenarioResource(scenario.id)}

    def _get_scenario_info(self) -> ShareScenarioInfoReponseDTO:
        """Fetch scenario metadata from a share link URL."""
        self.log_info_message(
            "Downloading the resource from a share link of another lab. Checking compatibility of the resource with the current lab"
        )

        response = requests.get(self._link, timeout=60)

        if response.status_code != 200:
            raise Exception("Error while getting information of the resource: " + response.text)

        try:
            return ShareScenarioInfoReponseDTO.from_json(response.json())
        except Exception as e:
            raise Exception(
                f"Error while parsing the scenario information from the share link. "
                f"The response format may be incompatible with this version of the lab. Details: {e}"
            ) from e

    def _get_request_headers(self) -> dict | None:
        """Share link flow uses no auth headers."""
        return None

    def run_after_task(self) -> None:
        super().run_after_task()

        if self.share_entity:
            self.log_info_message("Marking the resource as received in the origin lab")
            current_lab_info = ExternalLabApiService.get_current_lab_info(
                CurrentUserService.get_and_check_current_user()
            )

            response: requests.Response = ExternalLabApiService.mark_shared_object_as_received(
                self.share_entity.origin.lab_api_url,
                ShareLinkEntityType.SCENARIO,
                self.share_entity.token,
                current_lab_info,
                external_id=self._built_scenario_id,
            )

            if response.status_code != 200:
                self.log_error_message(
                    "Error while marking the resource as received: " + response.text
                )

    @classmethod
    def build_config(
        cls,
        link: str,
        mode: ScenarioDownloaderResourceMode,
        create_option: ScenarioDownloaderCreateOption,
        auto_run: bool = False,
        skip_scenario_tags: bool = False,
        skip_resource_tags: bool = False,
    ) -> ConfigParamsDict:
        return {
            "link": link,
            "resource_mode": mode,
            "create_option": create_option,
            "auto_run": auto_run,
            "skip_scenario_tags": skip_scenario_tags,
            "skip_resource_tags": skip_resource_tags,
        }

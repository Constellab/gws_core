import requests

from gws_core.config.config_params import ConfigParams, ConfigParamsDict
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.external_lab.external_lab_api_service import ExternalLabApiService
from gws_core.model.typing_style import TypingStyle
from gws_core.scenario.scenario_proxy import ScenarioProxy
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
    Task to download a scenario from another lab using a share link.

    This can be used between a dev and a prod environment of a lab.
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

        # verify that param are correct if we auto run
        auto_run = params["auto_run"]
        resource_mode: ScenarioDownloaderResourceMode = params["resource_mode"]
        # If we auto run we need to download input resource or all resource
        if auto_run and resource_mode not in ["Inputs only", "All"]:
            raise Exception("Auto run requires downloading input resources or all resources.")

        self._link = link
        self.share_entity = self._get_scenario_info()

        scenario = self._build_and_download_scenario(params, self.share_entity)

        if auto_run:
            self.log_info_message("Auto running the scenario")
            scenario_proxy = ScenarioProxy.from_existing_scenario(scenario.id)
            scenario_proxy.add_to_queue()

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

from typing import Literal

import requests

from gws_core.config.config_params import ConfigParams, ConfigParamsDict
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import BoolParam, StrParam
from gws_core.core.service.front_service import FrontService
from gws_core.core.utils.utils import Utils
from gws_core.external_lab.external_lab_api_service import ExternalLabApiService
from gws_core.io.io_spec import OutputSpec
from gws_core.io.io_specs import OutputSpecs
from gws_core.model.typing_style import TypingStyle
from gws_core.protocol.protocol_dto import ProtocolGraphConfigDTO
from gws_core.protocol.protocol_graph import ProtocolGraph
from gws_core.resource.resource_downloader import LabShareZipRouteDownloader
from gws_core.resource.resource_model import ResourceModel
from gws_core.scenario.scenario import Scenario
from gws_core.scenario.scenario_builder import ScenarioBuilder
from gws_core.scenario.task.scenario_resource import ScenarioResource
from gws_core.share.share_link import ShareLink
from gws_core.share.shared_dto import (
    ShareEntityCreateMode,
    ShareLinkEntityType,
    ShareScenarioInfoReponseDTO,
)
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs
from gws_core.user.current_user_service import CurrentUserService

ScenarioDownloaderResourceMode = Literal[
    "Inputs and outputs", "Inputs only", "Outputs only", "All", "None"
]
ScenarioDownloaderCreateOption = Literal["Skip if exists", "Force new scenario", "Update if exists"]


@task_decorator(
    unique_name="ScenarioDownloader",
    human_name="Download a scenario",
    short_description="Download a scenario from another lab using a link",
    style=TypingStyle.material_icon("scenario"),
)
class ScenarioDownloader(Task):
    """
    Task to download a scenario from another lab using a share link.

    This can be used between a dev and a prod environment of a lab.
    """

    output_specs = OutputSpecs({"scenario": OutputSpec(ScenarioResource, human_name="Scenario")})

    config_specs = ConfigSpecs(
        {
            "link": StrParam(
                human_name="Scenario link", short_description="Link to download the scenario"
            ),
            "resource_mode": StrParam(
                human_name="Resource mode",
                short_description="Mode for downloading resource of the scenario",
                allowed_values=Utils.get_literal_values(ScenarioDownloaderResourceMode),
            ),
            "create_option": StrParam(
                human_name="Create option",
                short_description="This applies for the scenario and the resources",
                allowed_values=Utils.get_literal_values(ScenarioDownloaderCreateOption),
                default_value="Skip if exists",
            ),
            "skip_scenario_tags": BoolParam(
                default_value=False,
                human_name="Skip scenario tags",
                short_description="If true, the scenario tags will not be set in the destination",
            ),
            "skip_resource_tags": BoolParam(
                default_value=False,
                human_name="Skip resource tags",
                short_description="If true, the resource tags will not be set in the destination",
            ),
        }
    )

    share_entity: ShareScenarioInfoReponseDTO
    _builder: ScenarioBuilder | None

    # define the percentage of the progress bar for each step
    INIT_EXP_PERCENT = 10
    DOWNLOAD_RESOURCE_PERCENT = 80
    BUILD_EXP_PERCENT = 10

    OUTPUT_NAME = "scenario"

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        link = params["link"]

        if not ShareLink.is_lab_share_scenario_link(link):
            raise Exception(
                "Invalid link, are you sure this a link of a share scenario from a lab ?"
            )

        self.share_entity = self._get_scenario_info(link)

        create_option = params["create_option"]
        create_mode: ShareEntityCreateMode = (
            ShareEntityCreateMode.NEW_ID
            if create_option == "Force new scenario"
            else ShareEntityCreateMode.KEEP_ID
        )

        existing_scenario = None
        is_update_mode = create_option == "Update if exists"

        # if we keep the scenario id, we check if the scenario already exists in the current lab
        if create_mode == ShareEntityCreateMode.KEEP_ID:
            scenario_model = Scenario.get_by_id(self.share_entity.entity_id)
            if scenario_model:
                if is_update_mode:
                    existing_scenario = scenario_model
                    self.log_info_message(
                        f"Scenario '{scenario_model.title}' already exists, will update it"
                    )
                else:
                    raise Exception(
                        "The scenario already exists in the current lab."
                        + f' <a href="{FrontService.get_scenario_url(scenario_model.id)}">Click here to view the existing scenario</a>.'
                    )

        self.update_progress_value(self.INIT_EXP_PERCENT, "Scenario information retrieved")

        scenario_info = self.share_entity.entity_object
        if not scenario_info.protocol.data.graph:
            raise Exception("The scenario protocol graph is missing.")
        resource_ids = self._get_resource_to_download(
            scenario_info.protocol.data.graph, params["resource_mode"]
        )

        zip_paths = self._download_resource_zips(resource_ids, self.share_entity, create_mode)

        self.update_progress_value(
            self.INIT_EXP_PERCENT + self.DOWNLOAD_RESOURCE_PERCENT, "Resources downloaded"
        )

        self._builder = ScenarioBuilder(
            scenario_info=scenario_info,
            resource_zip_paths=zip_paths,
            origin=self.share_entity.origin,
            create_mode=create_mode,
            message_dispatcher=self.get_message_dispatcher(),
            skip_resource_tags=params.get_value("skip_resource_tags"),
            skip_scenario_tags=params.get_value("skip_scenario_tags"),
        )

        scenario = self._builder.build()

        return {"scenario": ScenarioResource(scenario.id)}

    def _get_scenario_info(self, url: str) -> ShareScenarioInfoReponseDTO:
        """Fetch scenario metadata from a share link URL."""
        self.log_info_message(
            "Downloading the resource from a share link of another lab. Checking compatibility of the resource with the current lab"
        )

        response = requests.get(url, timeout=60)

        if response.status_code != 200:
            raise Exception("Error while getting information of the resource: " + response.text)
        return ShareScenarioInfoReponseDTO.from_json(response.json())

    def _get_resource_to_download(
        self, protocol_graph_dto: ProtocolGraphConfigDTO, mode: ScenarioDownloaderResourceMode
    ) -> set[str]:
        self.log_info_message(f"Getting the resources to download with option '{mode}'")

        if mode == "None":
            return set()

        protocol_graph = ProtocolGraph(protocol_graph_dto)

        if mode == "All":
            return protocol_graph.get_all_resource_ids()
        elif mode == "Inputs only":
            return protocol_graph.get_input_resource_ids()
        elif mode == "Outputs only":
            return protocol_graph.get_output_resource_ids()
        else:
            return protocol_graph.get_input_and_output_resource_ids()

    def _download_resource_zips(
        self,
        resource_ids: set[str],
        share_entity: ShareScenarioInfoReponseDTO,
        create_mode: ShareEntityCreateMode,
    ) -> dict[str, str]:
        """Download zip files for each resource that is not already present in the DB.

        Returns a dict mapping resource ID to local zip file path.
        """
        nb_resources = len(resource_ids)
        self.log_info_message(f"Downloading {nb_resources} resources")

        zip_paths: dict[str, str] = {}
        message_dispatcher = self.get_message_dispatcher()
        i = 1
        for resource_id in resource_ids:
            sub_dispatcher = message_dispatcher.create_sub_dispatcher(prefix=f"[Resource n°{i}] ")

            # In KEEP_ID mode skip download if the resource is already in the DB
            if create_mode == ShareEntityCreateMode.KEEP_ID:
                resource_model = ResourceModel.get_by_id(resource_id)
                if resource_model:
                    sub_dispatcher.notify_info_message(
                        f"Resource with id '{resource_id}' already exists in the current lab, skipping the download"
                    )
                    i += 1
                    continue

            current_percent = (
                self.INIT_EXP_PERCENT + ((i - 1) / nb_resources) * self.DOWNLOAD_RESOURCE_PERCENT
            )
            sub_dispatcher.notify_progress_value(
                current_percent, f"Downloading the resource '{resource_id}'."
            )

            url = share_entity.get_resource_route(resource_id)
            resource_downloader = LabShareZipRouteDownloader(url, sub_dispatcher)
            zip_path = resource_downloader.download()
            zip_paths[resource_id] = zip_path

            current_percent = (
                self.INIT_EXP_PERCENT + (i / nb_resources) * self.DOWNLOAD_RESOURCE_PERCENT
            )
            sub_dispatcher.notify_progress_value(
                current_percent, f"Resource '{resource_id}' downloaded"
            )

            i += 1

        return zip_paths

    def run_after_task(self) -> None:
        super().run_after_task()

        if self._builder:
            self._builder.cleanup()

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
        skip_scenario_tags: bool = False,
        skip_resource_tags: bool = False,
    ) -> ConfigParamsDict:
        return {
            "link": link,
            "resource_mode": mode,
            "create_option": create_option,
            "skip_scenario_tags": skip_scenario_tags,
            "skip_resource_tags": skip_resource_tags,
        }

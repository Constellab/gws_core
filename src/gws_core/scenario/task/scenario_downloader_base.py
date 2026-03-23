from abc import abstractmethod
from typing import Literal

from gws_core.config.config_params import ConfigParams
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import BoolParam, StrParam
from gws_core.core.service.external_api_service import ExternalApiService
from gws_core.core.service.front_service import FrontService
from gws_core.core.utils.utils import Utils
from gws_core.external_lab.external_lab_api_service import ExternalLabApiService
from gws_core.external_lab.external_lab_dto import MarkEntityAsSharedDTO
from gws_core.io.io_spec import OutputSpec
from gws_core.io.io_specs import OutputSpecs
from gws_core.protocol.protocol_dto import ProtocolGraphConfigDTO
from gws_core.protocol.protocol_graph import ProtocolGraph
from gws_core.resource.resource_downloader import LabShareZipRouteDownloader
from gws_core.resource.resource_model import ResourceModel
from gws_core.scenario.scenario import Scenario
from gws_core.scenario.scenario_builder import ScenarioBuilder
from gws_core.scenario.scenario_enums import ScenarioStatus
from gws_core.scenario.scenario_proxy import ScenarioProxy
from gws_core.scenario.task.scenario_resource import ScenarioResource
from gws_core.share.shared_dto import (
    ShareEntityCreateMode,
    ShareScenarioInfoReponseDTO,
)
from gws_core.task.task import Task
from gws_core.user.current_user_service import CurrentUserService

ScenarioDownloaderResourceMode = Literal[
    "Auto",
    "Inputs and outputs",
    "Inputs only",
    "Outputs only",
    "Inputs of draft tasks",
    "All",
    "None",
]
ScenarioDownloaderCreateOption = Literal["Update if exists", "Skip if exists", "Force new scenario"]


class ScenarioDownloaderBase(Task):
    """
    Base class for scenario download tasks. Contains shared logic for building
    a scenario from exported data and downloading resources.

    Subclasses must implement:
    - `_get_scenario_info()` — how to fetch scenario metadata
    - `_get_request_headers()` — headers for resource download requests
    """

    output_specs = OutputSpecs({"scenario": OutputSpec(ScenarioResource, human_name="Scenario")})

    config_specs = ConfigSpecs(
        {
            "resource_mode": StrParam(
                human_name="Resource mode",
                short_description="Mode for downloading resource of the scenario",
                allowed_values=Utils.get_literal_values(ScenarioDownloaderResourceMode),
                default_value="Auto",
            ),
            "create_option": StrParam(
                human_name="Create option",
                short_description="This applies for the scenario and the resources",
                allowed_values=Utils.get_literal_values(ScenarioDownloaderCreateOption),
                default_value="Update if exists",
            ),
            "auto_run": BoolParam(
                default_value=False,
                human_name="Run scenario after download",
                short_description="If true, the scenario will be automatically run after download",
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
    _built_scenario_id: str | None

    # define the percentage of the progress bar for each step
    INIT_EXP_PERCENT = 10
    DOWNLOAD_RESOURCE_PERCENT = 80
    BUILD_EXP_PERCENT = 10

    OUTPUT_NAME = "scenario"

    @abstractmethod
    def _get_scenario_info(self) -> ShareScenarioInfoReponseDTO:
        """Fetch scenario metadata. Implemented by subclasses."""

    @abstractmethod
    def _get_request_headers(self) -> dict | None:
        """Return headers for resource download requests.
        Returns None for share link flow, auth headers for credential flow.
        """

    def _get_resource_to_download(
        self, protocol_graph_dto: ProtocolGraphConfigDTO, mode: ScenarioDownloaderResourceMode
    ) -> set[str]:
        self.log_info_message(f"Getting the resources to download with option '{mode}'")

        if mode == "None":
            return set()

        protocol_graph = ProtocolGraph(protocol_graph_dto)

        mode_methods = {
            "All": protocol_graph.get_all_resource_ids,
            "Inputs only": protocol_graph.get_input_resource_ids,
            "Outputs only": protocol_graph.get_output_resource_ids,
            "Inputs and outputs": protocol_graph.get_input_and_output_resource_ids,
            "Inputs of draft tasks": protocol_graph.get_input_resource_ids_of_draft_tasks,
        }

        return mode_methods.get(mode, protocol_graph.get_input_and_output_resource_ids)()

    def _resolve_auto_resource_mode(
        self, share_entity: ShareScenarioInfoReponseDTO, auto_run: bool
    ) -> ScenarioDownloaderResourceMode:
        """Resolve the 'Auto' resource mode based on the scenario status.

        - DRAFT: download inputs only (scenario hasn't been run yet)
        - SUCCESS: download outputs only (scenario finished successfully)
        - RUNNING: download outputs only (grab available outputs)
        - PARTIALLY_RUN: download inputs of draft tasks (only tasks not yet run need their inputs)
        - Other statuses: download inputs and outputs as a safe default
        """
        if auto_run:
            return (
                "Inputs of draft tasks"  # If we auto run we need at least the input of draft tasks
            )
        scenario_status = share_entity.entity_object.scenario.status

        status_to_mode: dict[ScenarioStatus, ScenarioDownloaderResourceMode] = {
            ScenarioStatus.DRAFT: "Inputs only",
            ScenarioStatus.SUCCESS: "Outputs only",
            ScenarioStatus.RUNNING: "Outputs only",
            ScenarioStatus.PARTIALLY_RUN: "Inputs of draft tasks",
        }

        resolved_mode = status_to_mode.get(scenario_status, "Inputs and outputs")
        self.log_info_message(
            f"Auto resource mode resolved to '{resolved_mode}' based on scenario status '{scenario_status.value}'"
        )
        return resolved_mode

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
        headers = self._get_request_headers()
        i = 1
        for resource_id in resource_ids:
            sub_dispatcher = message_dispatcher.create_sub_dispatcher(prefix=f"[Resource n°{i}] ")

            # In KEEP_ID mode skip download if the resource is already in the DB and has content
            if create_mode == ShareEntityCreateMode.KEEP_ID:
                resource_model = ResourceModel.get_by_id(resource_id)
                if resource_model and not resource_model.content_is_deleted:
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
            resource_downloader = LabShareZipRouteDownloader(url, sub_dispatcher, headers=headers)
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

    def _build_and_download_scenario(
        self, params: ConfigParams, share_entity: ShareScenarioInfoReponseDTO
    ) -> Scenario:
        """Shared logic: check existing scenario, build scenario, download resources, fill zips.

        Returns the built Scenario model.
        """
        auto_run = params["auto_run"]
        resource_mode: ScenarioDownloaderResourceMode = params["resource_mode"]

        # Resolve "Auto" mode based on the scenario status
        if resource_mode == "Auto":
            resource_mode = self._resolve_auto_resource_mode(share_entity, auto_run)

        # If we auto run we need to download input resource or all resource
        if auto_run and resource_mode not in [
            "Inputs only",
            "Inputs and outputs",
            "All",
            "Inputs of draft tasks",
        ]:
            raise Exception(
                f"Auto run requires downloading input resources or all resources. Current mode: '{resource_mode}'."
            )

        create_option = params["create_option"]
        create_mode: ShareEntityCreateMode = (
            ShareEntityCreateMode.NEW_ID
            if create_option == "Force new scenario"
            else ShareEntityCreateMode.KEEP_ID
        )

        is_update_mode = create_option == "Update if exists"

        # if we keep the scenario id, we check if the scenario already exists in the current lab
        if create_mode == ShareEntityCreateMode.KEEP_ID:
            scenario_model = Scenario.get_by_id(share_entity.entity_id)
            if scenario_model:
                if is_update_mode:
                    self.log_info_message(
                        f"Scenario '{scenario_model.title}' already exists, will update it"
                    )
                else:
                    raise Exception(
                        "The scenario already exists in the current lab."
                        + f' <a href="{FrontService().get_scenario_url(scenario_model.id)}">Click here to view the existing scenario</a>.'
                    )

        self.update_progress_value(self.INIT_EXP_PERCENT, "Scenario information retrieved")

        scenario_info = share_entity.entity_object
        if not scenario_info.protocol.data.graph:
            raise Exception("The scenario protocol graph is missing.")
        self._builder = ScenarioBuilder(
            scenario_info=scenario_info,
            origin=share_entity.origin,
            create_mode=create_mode,
            message_dispatcher=self.get_message_dispatcher(),
            skip_resource_tags=params.get_value("skip_resource_tags"),
            skip_scenario_tags=params.get_value("skip_scenario_tags"),
        )

        scenario = self._builder.build()

        # Download and fill resource content after the scenario is built
        resource_ids = self._get_resource_to_download(
            scenario_info.protocol.data.graph, resource_mode
        )

        zip_paths = self._download_resource_zips(resource_ids, share_entity, create_mode)

        self.update_progress_value(
            self.INIT_EXP_PERCENT + self.DOWNLOAD_RESOURCE_PERCENT, "Resources downloaded"
        )

        self._builder.fill_zip_resources(zip_paths)

        self._built_scenario_id = scenario.id

        # Mark each downloaded resource as shared in the origin lab
        self._mark_resources_as_shared(share_entity, zip_paths)

        if auto_run:
            self.log_info_message("Auto running the scenario")
            scenario_proxy = ScenarioProxy.from_existing_scenario(scenario.id)
            if scenario_proxy.is_running():
                scenario_proxy.stop_or_remove_from_queue()  # Force stop the scenario in case it's marked as running
            if scenario_proxy.is_finished():
                # Force reset the scenario so it is not marked as running
                scenario_proxy.reset_error_processes()
            scenario_proxy.add_to_queue()

        return scenario

    def _mark_resources_as_shared(
        self,
        share_entity: ShareScenarioInfoReponseDTO,
        resource_zip_paths: dict[str, str],
    ) -> None:
        """Mark each downloaded resource as shared in the origin lab."""
        if not resource_zip_paths:
            return

        self.log_info_message("Marking resources as shared in the origin lab")

        current_lab_info = ExternalLabApiService.get_current_lab_info(
            CurrentUserService.get_and_check_current_user()
        )
        headers = self._get_request_headers()

        for resource_id in resource_zip_paths:
            body = MarkEntityAsSharedDTO(
                lab_info=current_lab_info,
                external_id=resource_id,
            )
            url = share_entity.get_mark_as_shared_route(resource_id)

            try:
                ExternalApiService.post(
                    url,
                    body=body.to_json_dict(),
                    headers=headers,
                    raise_exception_if_error=True,
                )
            except Exception as e:
                self.log_error_message(
                    f"Error while marking resource '{resource_id}' as shared: {e}"
                )

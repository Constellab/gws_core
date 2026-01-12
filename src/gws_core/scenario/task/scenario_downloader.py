from typing import Literal, cast

import requests

from gws_core.config.config_params import ConfigParams, ConfigParamsDict
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.db.gws_core_db_manager import GwsCoreDbManager
from gws_core.core.service.front_service import FrontService
from gws_core.core.utils.utils import Utils
from gws_core.external_lab.external_lab_api_service import ExternalLabApiService
from gws_core.io.io_spec import OutputSpec
from gws_core.io.io_specs import OutputSpecs
from gws_core.io.port import Port
from gws_core.model.typing_style import TypingStyle
from gws_core.protocol.protocol_dto import ProtocolGraphConfigDTO
from gws_core.protocol.protocol_graph import ProtocolGraph
from gws_core.resource.resource import Resource
from gws_core.resource.resource_downloader import LabShareZipRouteDownloader
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_loader import ResourceLoader
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.resource_set.resource_list_base import ResourceListBase
from gws_core.scenario.scenario import Scenario
from gws_core.scenario.scenario_loader import ScenarioLoader
from gws_core.scenario.scenario_zipper import ZipScenarioInfo
from gws_core.scenario.task.scenario_resource import ScenarioResource
from gws_core.share.share_link import ShareLink
from gws_core.share.shared_dto import (
    SharedEntityMode,
    ShareEntityCreateMode,
    ShareLinkEntityType,
    ShareScenarioInfoReponseDTO,
)
from gws_core.share.shared_resource import SharedResource
from gws_core.share.shared_scenario import SharedScenario
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.tag_entity_type import TagEntityType
from gws_core.task.plug.input_task import InputTask
from gws_core.task.plug.output_task import OutputTask
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs
from gws_core.task.task_model import TaskModel
from gws_core.user.current_user_service import CurrentUserService

ScenarioDownloaderResourceMode = Literal[
    "Inputs and outputs", "Inputs only", "Outputs only", "All", "None"
]
ScenarioDownloaderCreateOption = Literal["Skip if exists", "Force new scenario"]


class ImportedResource:
    old_id: str
    resource: Resource
    children: dict[str, Resource]

    def __init__(self, old_id: str, resource: Resource, children: dict[str, Resource]):
        self.old_id = old_id
        self.resource = resource
        self.children = children


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
        }
    )

    share_entity: ShareScenarioInfoReponseDTO
    resource_loaders: list[ResourceLoader]
    resource_models: dict[str, ResourceModel]

    downloaded_resources: dict[str, ImportedResource]

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

        self.share_entity = self.get_scenario_info(link)

        create_option = params["create_option"]
        create_mode: ShareEntityCreateMode = (
            ShareEntityCreateMode.NEW_ID
            if create_option == "Force new scenario"
            else ShareEntityCreateMode.KEEP_ID
        )

        # if we keep the scenario id, we check if the scenario already exists in the current lab
        if create_mode == ShareEntityCreateMode.KEEP_ID:
            scenario_model = Scenario.get_by_id(self.share_entity.entity_id)
            if scenario_model:
                raise Exception(
                    "The scenario already exists in the current lab."
                    + f' <a href="{FrontService.get_scenario_url(scenario_model.id)}">Click here to view the existing scenario</a>.'
                )

        self.update_progress_value(self.INIT_EXP_PERCENT, "Scenario information retrieved")

        scenario_info = self.share_entity.entity_object
        if not scenario_info.protocol.data.graph:
            raise Exception("The scenario protocol graph is missing.")
        resource_ids = self.get_resource_to_download(
            scenario_info.protocol.data.graph, params["resource_mode"]
        )

        self.download_resources(resource_ids, self.share_entity, create_mode)

        self.update_progress_value(
            self.INIT_EXP_PERCENT + self.DOWNLOAD_RESOURCE_PERCENT, "Resources downloaded"
        )

        scenario_loader = self.load_scenario(scenario_info, create_mode)

        scenario = self.build_scenario(scenario_loader)

        return {"scenario": ScenarioResource(scenario.id)}

    def get_scenario_info(self, url: str) -> ShareScenarioInfoReponseDTO:
        """If the link is a share link from a lab, check the compatibility of the resource with the current lab,
        then zip the resource and return the download url
        """
        self.log_info_message(
            "Downloading the resource from a share link of another lab. Checking compatibility of the resource with the current lab"
        )

        response = requests.get(url, timeout=60)

        if response.status_code != 200:
            raise Exception("Error while getting information of the resource: " + response.text)
        return ShareScenarioInfoReponseDTO.from_json(response.json())

    def load_scenario(
        self, scenario_info: ZipScenarioInfo, create_mode: ShareEntityCreateMode
    ) -> ScenarioLoader:
        self.log_info_message("Loading the scenario")
        scenario_loader = ScenarioLoader(scenario_info, create_mode, self.message_dispatcher)

        scenario_loader.load_scenario()

        return scenario_loader

    def get_resource_to_download(
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

    def download_resources(
        self,
        resource_ids: set[str],
        share_entity: ShareScenarioInfoReponseDTO,
        create_mode: ShareEntityCreateMode,
    ) -> None:
        self.resource_loaders = []
        self.resource_models = {}
        self.downloaded_resources = {}

        nb_resources = len(resource_ids)
        self.log_info_message(f"Downloading {nb_resources} resources")

        i = 1
        for resource_id in resource_ids:
            # create a sub dispatcher to define a prefix
            sub_dispatcher = self.message_dispatcher.create_sub_dispatcher(
                prefix=f"[Resource n°{i}]"
            )

            # if the KEEP_ID mode is activated, and the resource exists in the current lab, skip the download
            if create_mode == ShareEntityCreateMode.KEEP_ID:
                resource_model = ResourceModel.get_by_id(resource_id)
                if resource_model:
                    # don't add the resource to the downloaded resources because we don't want to save it
                    sub_dispatcher.notify_info_message(
                        f"Resource with id '{resource_id}' already exists in the current lab, skipping the download"
                    )
                    self.resource_models[resource_id] = resource_model

            # if the resource is not already in the current lab, download it
            if resource_id not in self.resource_models:
                current_percent = (
                    self.INIT_EXP_PERCENT
                    + ((i - 1) / nb_resources) * self.DOWNLOAD_RESOURCE_PERCENT
                )
                sub_dispatcher.notify_progress_value(current_percent, "Downloading the resource.")

                url = share_entity.get_resource_route(resource_id)
                self.download_resource(url, sub_dispatcher, create_mode)

            current_percent = (
                self.INIT_EXP_PERCENT + ((i) / nb_resources) * self.DOWNLOAD_RESOURCE_PERCENT
            )
            sub_dispatcher.notify_progress_value(current_percent, "Resource loaded")

            i += 1

    def download_resource(
        self,
        download_url: str,
        message_dispatcher: MessageDispatcher,
        create_mode: ShareEntityCreateMode,
    ) -> Resource:
        # ScenarioDownloader receives zip route URLs, not resource info URLs
        resource_downloader = LabShareZipRouteDownloader(download_url, message_dispatcher)

        # download the resource file
        resource_file = resource_downloader.download()

        message_dispatcher.notify_info_message("Loading the resource")
        resource_loader = ResourceLoader.from_compress_file(resource_file, create_mode)

        # store the loader to clean at the end
        self.resource_loaders.append(resource_loader)

        resource = resource_loader.load_resource()

        imported_resource = ImportedResource(
            resource_loader.get_main_resource_origin_id(),
            resource,
            resource_loader.get_generated_children_resources(),
        )
        self.downloaded_resources[imported_resource.old_id] = imported_resource

        return resource

    @GwsCoreDbManager.transaction()
    def build_scenario(self, scenario_load: ScenarioLoader) -> Scenario:
        self.log_info_message("Building the scenario")

        scenario = scenario_load.get_scenario()

        protocol_model = scenario_load.get_protocol_model()

        scenario.save()
        protocol_model.save_full()

        self.log_info_message("Saving the scenario tags")
        tags = scenario_load.get_tags()
        # set the lab origin for the tags
        for tag in tags:
            tag.set_external_lab_origin(self.share_entity.origin.lab_id)
        # Add tags
        entity_tags: EntityTagList = EntityTagList(TagEntityType.SCENARIO, scenario.id)
        entity_tags.add_tags(tags)

        self.log_info_message("Saving the resources")

        # then we save other resources
        # we sort the process by start date to save the resources in the right order
        for process_model in protocol_model.get_all_processes_flatten_sort_by_start_date():
            # for Input process, update the config with new resource id
            if process_model.is_input_task():
                # save input resources and update the config with the new resource id
                resource_model_id = process_model.out_port(
                    InputTask.output_name
                ).get_resource_model_id()

                resource_model = self.save_resource_and_children(resource_model_id, flagged=True)

                new_resource_id = resource_model.id if resource_model else None
                process_model.set_config_value(InputTask.config_name, new_resource_id)

            elif isinstance(process_model, TaskModel):
                # save all the resources generated by the process
                for port_name, out_port in process_model.outputs.ports.items():
                    old_resource_id = out_port.get_resource_model_id()

                    self.save_resource_and_children(
                        old_resource_id, process_model, scenario, port_name
                    )

            # update the resources in the ports
            self.update_ports_resources(cast(dict[str, Port], process_model.inputs.ports))
            self.update_ports_resources(cast(dict[str, Port], process_model.outputs.ports))

            # create TaskInputModel
            if isinstance(process_model, TaskModel):
                process_model.save_input_resources()

            # mark the output resource as flagged
            if process_model.is_output_task():
                resource_model = process_model.in_port(OutputTask.input_name).get_resource_model()
                if resource_model:
                    resource_model.flagged = True
                    resource_model.save()

        protocol_model.save_full()

        # Create the shared entity info
        self.log_info_message("Storing the scenario origin info")
        SharedScenario.create_from_lab_info(
            scenario.id,
            SharedEntityMode.RECEIVED,
            self.share_entity.origin,
            CurrentUserService.get_and_check_current_user(),
        )

        return scenario

    def save_resource_and_children(
        self,
        old_resource_id: str | None,
        task_model: TaskModel | None = None,
        scenario: Scenario | None = None,
        task_port_name: str | None = None,
        flagged: bool = False,
    ) -> ResourceModel | None:
        if not old_resource_id:
            return None

        if old_resource_id in self.resource_models:
            return self.resource_models[old_resource_id]

        downloaded_resource = self.downloaded_resources.get(old_resource_id)
        # if the resource was not downloaded, we skip it
        if not downloaded_resource:
            return None

        # first save the children resources
        children_resource_models: list[ResourceModel] = []
        if len(downloaded_resource.children) > 0 and isinstance(
            downloaded_resource.resource, ResourceListBase
        ):
            # dict where key is resource uid and value is the new saved resource object
            new_children_resources: dict[str, Resource] = {}
            for child_old_id, child_resource in downloaded_resource.children.items():
                # If the children was already saved, we skip it
                # This happens if the children was not created by the current task but already exist before
                # when create_new_resource=False during the resource set building
                if child_old_id in self.resource_models:
                    new_children_resources[child_resource.uid] = self.resource_models[
                        child_old_id
                    ].get_resource()
                    continue
                child_model = self.save_resource(
                    child_old_id, child_resource, task_model, scenario, task_port_name
                )
                new_children_resources[child_resource.uid] = child_model.get_resource()
                children_resource_models.append(child_model)
            downloaded_resource.resource.__set_r_field__(new_children_resources)

        resource_model = self.save_resource(
            old_resource_id,
            downloaded_resource.resource,
            task_model,
            scenario,
            task_port_name,
            flagged,
        )
        self.resource_models[old_resource_id] = resource_model

        # set the parent id of the children resources
        for child_model in children_resource_models:
            child_model.set_parent_and_save(resource_model.id)

        return resource_model

    def save_resource(
        self,
        old_resource_id: str,
        resource: Resource,
        task_model: TaskModel | None = None,
        scenario: Scenario | None = None,
        task_port_name: str | None = None,
        flagged: bool = False,
    ) -> ResourceModel:
        if old_resource_id in self.resource_models:
            return self.resource_models[old_resource_id]

        resource_model = ResourceModel.save_from_resource(
            resource,
            origin=ResourceOrigin.IMPORTED_FROM_LAB,
            scenario=scenario,
            task_model=task_model,
            port_name=task_port_name,
            flagged=flagged,
        )

        # save the origin for the input resource
        SharedResource.create_from_lab_info(
            resource_model.id,
            SharedEntityMode.RECEIVED,
            self.share_entity.origin,
            CurrentUserService.get_and_check_current_user(),
        )

        self.resource_models[old_resource_id] = resource_model
        return resource_model

    def update_ports_resources(self, ports: dict[str, Port]) -> None:
        for port in ports.values():
            old_resource_id = port.get_resource_model_id()

            if old_resource_id in self.resource_models:
                port.set_resource_model(self.resource_models[old_resource_id])
            else:
                port.set_resource_model(None)

    def run_after_task(self) -> None:
        super().run_after_task()

        if self.resource_loaders:
            for resource_loader in self.resource_loaders:
                resource_loader.delete_resource_folder()

        if self.share_entity:
            self.log_info_message("Marking the resource as received in the origin lab")
            # call the origin lab to mark the scenario as received
            current_lab_info = ExternalLabApiService.get_current_lab_info(
                CurrentUserService.get_and_check_current_user()
            )

            # retrieve the token which is the last part of the link
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
    ) -> ConfigParamsDict:
        return {"link": link, "resource_mode": mode, "create_option": create_option}

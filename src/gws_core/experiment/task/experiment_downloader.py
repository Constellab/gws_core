

from typing import Dict, List, Literal, Set

import requests

from gws_core.config.config_params import ConfigParams
from gws_core.config.config_types import ConfigParamsDict, ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.decorator.transaction import transaction
from gws_core.core.service.external_lab_service import ExternalLabService
from gws_core.core.utils.utils import Utils
from gws_core.experiment.experiement_loader import ExperimentLoader
from gws_core.experiment.experiment import Experiment
from gws_core.experiment.experiment_zipper import ZipExperimentInfo
from gws_core.experiment.task.experiment_resource import ExperimentResource
from gws_core.io.io_spec import OutputSpec
from gws_core.io.io_specs import OutputSpecs
from gws_core.model.typing_style import TypingStyle
from gws_core.protocol.protocol_dto import ProtocolGraphConfigDTO
from gws_core.protocol.protocol_graph import ProtocolGraph
from gws_core.resource.resource import Resource
from gws_core.resource.resource_downloader import ResourceDownloader
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_loader import ResourceLoader
from gws_core.resource.resource_model import ResourceModel
from gws_core.share.share_link import ShareLink
from gws_core.share.shared_dto import (SharedEntityMode,
                                       ShareExperimentInfoReponseDTO,
                                       ShareLinkType)
from gws_core.share.shared_experiment import SharedExperiment
from gws_core.share.shared_resource import SharedResource
from gws_core.task.plug import Source
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs
from gws_core.task.task_model import TaskModel
from gws_core.user.current_user_service import CurrentUserService

ExperimentDownloaderMode = Literal['Inputs and outputs', 'Inputs only', 'Outputs only', 'All', 'None']


@task_decorator(unique_name="ExperimentDownloader", human_name="Download an experiment",
                short_description="Download an experiment from another lab using a link",
                style=TypingStyle.material_icon("experiment"))
class ExperimentDownloader(Task):

    output_specs = OutputSpecs({
        'experiment': OutputSpec(ExperimentResource, human_name='Experiment')
    })

    config_specs: ConfigSpecs = {
        'link': StrParam(human_name='Resource link', short_description='Link to download the resource'),
        'resource_mode': StrParam(human_name='Resource mode', short_description='Mode for downloading resource of the experiment',
                                  allowed_values=Utils.get_literal_values(ExperimentDownloaderMode))
    }

    share_entity: ShareExperimentInfoReponseDTO
    resource_loaders: List[ResourceLoader]

    # define the percentage of the progress bar for each step
    INIT_EXP_PERCENT = 10
    DOWNLOAD_RESOURCE_PERCENT = 80
    BUILD_EXP_PERCENT = 10

    OUTPUT_NAME = 'experiment'

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        link = params['link']

        if not ShareLink.is_lab_share_experiment_link(link):
            raise Exception("Invalid link, are you sure this a link of a share experiment from a lab ?")

        self.share_entity = self.get_experiment_info(link)

        self.update_progress_value(self.INIT_EXP_PERCENT, 'Experiment information retrieved')

        exp_info = self.share_entity.entity_object
        resource_ids = self.get_resource_to_download(exp_info.protocol.data.graph, params['resource_mode'])

        resources = self.download_resources(resource_ids, self.share_entity)

        self.update_progress_value(self.INIT_EXP_PERCENT + self.DOWNLOAD_RESOURCE_PERCENT, 'Resources downloaded')

        experiment_loader = self.load_experiment(exp_info)

        experiment = self.build_experiment(experiment_loader, resources)

        return {'experiment': ExperimentResource(experiment.id)}

    def get_experiment_info(self, url: str) -> ShareExperimentInfoReponseDTO:
        """If the link is a share link from a lab, check the compatibility of the resource with the current lab,
        then zip the resource and return the download url
        """
        self.log_info_message(
            "Downloading the resource from a share link of another lab. Checking compatibility of the resource with the current lab")

        response = requests.get(url, timeout=60)

        if response.status_code != 200:
            raise Exception("Error while getting information of the resource: " + response.text)
        return ShareExperimentInfoReponseDTO.from_json(response.json())

    def load_experiment(self, experiment_info: ZipExperimentInfo) -> ExperimentLoader:

        self.log_info_message("Loading the experiment")
        experiment_loader = ExperimentLoader(experiment_info, self.message_dispatcher)

        experiment_loader.load_experiment()

        return experiment_loader

    def get_resource_to_download(
            self, protocol_graph_dto: ProtocolGraphConfigDTO, mode: ExperimentDownloaderMode) -> Set[str]:

        self.log_info_message(f"Getting the resources to download with option '{mode}'")

        if mode == 'None':
            return set()

        protocol_graph = ProtocolGraph(protocol_graph_dto)

        if mode == 'All':
            return protocol_graph.get_all_resource_ids()
        elif mode == 'Inputs only':
            return protocol_graph.get_input_resource_ids()
        elif mode == 'Outputs only':
            return protocol_graph.get_output_resource_ids()
        else:
            return protocol_graph.get_input_and_output_resource_ids()

    def download_resources(self, resource_ids: Set[str],
                           share_entity: ShareExperimentInfoReponseDTO) -> Dict[str, Resource]:
        self.resource_loaders = []

        resources: Dict[str, Resource] = {}

        nb_resources = len(resource_ids)
        self.log_info_message(f"Downloading {nb_resources} resources")

        i = 1
        for resource_id in resource_ids:
            # create a sub dispatcher to define a prefix
            sub_dispatcher = self.message_dispatcher.create_sub_dispatcher(prefix=f"[Resource n°{i}]")
            current_percent = self.INIT_EXP_PERCENT + ((i - 1) / nb_resources) * self.DOWNLOAD_RESOURCE_PERCENT
            sub_dispatcher.notify_progress_value(current_percent,  "Downloading the resource.")

            url = share_entity.get_resource_route(resource_id)
            resources[resource_id] = self.download_resource(url, sub_dispatcher)

            current_percent = self.INIT_EXP_PERCENT + ((i) / nb_resources) * self.DOWNLOAD_RESOURCE_PERCENT
            sub_dispatcher.notify_progress_value(current_percent, "Resource loaded")

            i += 1
        return resources

    def download_resource(self, download_url: str, message_dispatcher: MessageDispatcher) -> Resource:

        resource_downloader = ResourceDownloader(message_dispatcher)

        # download the resource file
        download_route = resource_downloader.call_zip_resource(download_url)

        resource_file = resource_downloader.download_resource(download_route)

        message_dispatcher.notify_info_message("Loading the resource")
        resource_loader = ResourceLoader.from_compress_file(resource_file)

        # store the loader to clean at the end
        self.resource_loaders.append(resource_loader)

        resource = resource_loader.load_resource()

        return resource

    @transaction()
    def build_experiment(self, experiment_load: ExperimentLoader, resources: Dict[str, Resource]) -> Experiment:

        self.log_info_message("Building the experiment")

        experiment = experiment_load.get_experiment()

        protocol_model = experiment_load.get_protocol_model()

        experiment.save()
        protocol_model.save_full()

        resource_models: Dict[str, ResourceModel] = {}

        self.log_info_message("Replacing the resources in the protocol by the downloaded resources")

        # first, we save the inputs of protocol
        inputs = protocol_model.get_source_resource_ids()
        for resource_id in inputs:
            if resource_id in resources:
                resource = resources[resource_id]
                resource_model = ResourceModel.save_from_resource(resource, origin=ResourceOrigin.IMPORTED_FROM_LAB)
                resource_models[resource_id] = resource_model

                # save the origin for the input resource
                SharedResource.create_from_lab_info(resource_model.id, SharedEntityMode.RECEIVED,
                                                    self.share_entity.origin,
                                                    CurrentUserService.get_and_check_current_user())

        # then we save other resources
        # we sort the process by start date to save the resources in the right order
        for process_model in protocol_model.get_all_processes_flatten_sort_by_start_date():

            # first we save the inputs
            for port_name, in_port in process_model.inputs.ports.items():
                old_resource_id = in_port.get_resource_model_id()

                if old_resource_id:
                    # retrieve the resource from the already saved resources
                    # set the resource model in the input port
                    resource_model = resource_models.get(old_resource_id)
                    in_port.set_resource_model(resource_model)

                    # if the resource is an output, flag it
                    if resource_model and isinstance(process_model, TaskModel) and process_model.is_sink_task():
                        resource_model.flagged = True
                        resource_model.save()

                else:
                    in_port.set_resource_model(None)

            # save the TaskInputModel
            if isinstance(process_model, TaskModel):
                process_model.save_input_resources()

            # then we save the outputs
            for port_name, out_port in process_model.outputs.ports.items():

                output_old_resource_id = out_port.get_resource_model_id()
                if output_old_resource_id and output_old_resource_id in resources:
                    # get the resource model, if we are in a protocol or the output is constant,
                    # the resource model should already be saved
                    # otherwise, we save it with the task model
                    output_resource_model = resource_models.get(output_old_resource_id)

                    if output_resource_model is None and isinstance(process_model, TaskModel):
                        output_resource_model = process_model.save_output_resource(
                            resources[output_old_resource_id], port_name)
                        # save it in the resource_models dict
                        resource_models[output_old_resource_id] = output_resource_model

                    if output_resource_model is None:
                        raise Exception(
                            f"Error while building the experiment: Resource '{output_old_resource_id}' not found")

                    out_port.set_resource_model(output_resource_model)

                else:
                    out_port.set_resource_model(None)

            # for Source process, update the config with new resource id
            if isinstance(process_model, TaskModel) and process_model.is_source_task():
                new_resource = process_model.out_port(Source.output_name).get_resource_model()
                new_resource_id = new_resource.id if new_resource else None
                process_model.set_config_value(Source.config_name, new_resource_id)

        protocol_model.save_full()

        # Create the shared entity info
        self.log_info_message("Storing the expeirment origin info")
        SharedExperiment.create_from_lab_info(experiment.id, SharedEntityMode.RECEIVED,
                                              self.share_entity.origin,
                                              CurrentUserService.get_and_check_current_user())

        return experiment

    def run_after_task(self) -> None:
        super().run_after_task()

        if self.resource_loaders:
            for resource_loader in self.resource_loaders:
                resource_loader.delete_resource_folder()

        if self.share_entity:
            self.log_info_message(
                "Marking the resource as received in the origin lab")
            # call the origin lab to mark the experiment as received
            current_lab_info = ExternalLabService.get_current_lab_info(
                CurrentUserService.get_and_check_current_user())

            # retrieve the token which is the last part of the link
            response: requests.Response = ExternalLabService.mark_shared_object_as_received(
                self.share_entity.origin.lab_api_url,
                ShareLinkType.EXPERIMENT, self.share_entity.token, current_lab_info)

            if response.status_code != 200:
                self.log_error_message(
                    "Error while marking the resource as received: " + response.text)

    @classmethod
    def build_config(cls, link: str, mode: ExperimentDownloaderMode) -> ConfigParamsDict:
        return {
            'link': link,
            'resource_mode': mode
        }

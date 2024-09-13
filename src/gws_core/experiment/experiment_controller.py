
from typing import Dict, List, Optional

from fastapi import Depends

from gws_core.core.classes.search_builder import SearchParams
from gws_core.core.model.model_dto import BaseModelDTO, PageDTO
from gws_core.entity_navigator.entity_navigator_dto import ImpactResultDTO
from gws_core.entity_navigator.entity_navigator_service import \
    EntityNavigatorService
from gws_core.experiment.experiment_downloader_service import \
    ExperimentDownloaderService
from gws_core.experiment.task.experiment_downloader import \
    ExperimentDownloaderMode

from ..core_controller import core_app
from ..user.auth_service import AuthService
from .experiment_dto import (ExperimentCountByTitleResultDTO, ExperimentDTO,
                             ExperimentSaveDTO, RunningExperimentInfoDTO)
from .experiment_run_service import ExperimentRunService
from .experiment_service import ExperimentService
from .queue_service import QueueService

###################################### GET ###############################


@core_app.get("/experiment/running", tags=["Experiment"],
              summary="Get the list of running experiments")
def get_the_list_of_running_experiments(
        _=Depends(AuthService.check_user_access_token)) -> List[RunningExperimentInfoDTO]:
    """
    Retrieve a list of running experiments.
    """

    return ExperimentService.get_running_experiments()


@core_app.get("/experiment/{id_}", tags=["Experiment"], summary="Get an experiment")
def get_an_experiment(id_: str,
                      _=Depends(AuthService.check_user_access_token)) -> ExperimentDTO:
    """
    Retrieve an experiment

    - **id_**: the id_ of an experiment
    """

    return ExperimentService.get_by_id_and_check(id_).to_dto()


@core_app.post("/experiment/advanced-search", tags=["Experiment"], summary="Advanced search for experiment")
def advanced_search(search_dict: SearchParams,
                    page: Optional[int] = 1,
                    number_of_items_per_page: Optional[int] = 20,
                    _=Depends(AuthService.check_user_access_token)) -> PageDTO[ExperimentDTO]:
    """
    Advanced search on experiment
    """
    return ExperimentService.search(search_dict, page, number_of_items_per_page).to_dto()


@core_app.get("/experiment/title/{title}/count", tags=["Experiment"], summary="Count experiment by title")
def count_by_title(title: str,
                   _=Depends(AuthService.check_user_access_token)) -> ExperimentCountByTitleResultDTO:
    return ExperimentCountByTitleResultDTO(count=ExperimentService.count_by_title(title))


@core_app.get("/experiment/search-title/{title}", tags=["Experiment"], summary="Search experiment by title")
def search_by_title(title: str,
                    page: Optional[int] = 1,
                    number_of_items_per_page: Optional[int] = 20,
                    _=Depends(AuthService.check_user_access_token)) -> PageDTO[ExperimentDTO]:
    """
    Advanced search on experiment
    """
    return ExperimentService.search_by_title(title, page, number_of_items_per_page).to_dto()


@core_app.get("/experiment/input-resource/{resource_id}", tags=["Experiment"],
              summary="Get the list of experiments by input resource")
def get_by_input_resource(resource_id: str,
                          page: Optional[int] = 1,
                          number_of_items_per_page: Optional[int] = 20,
                          _=Depends(AuthService.check_user_access_token)) -> PageDTO[ExperimentDTO]:
    """
    Retrieve a list of experiments by the input resource
    """

    return ExperimentService.get_next_experiments_of_resource(
        resource_id=resource_id,
        page=page,
        number_of_items_per_page=number_of_items_per_page,
    ).to_dto()


###################################### CREATE ################################

@core_app.post("/experiment", tags=["Experiment"], summary="Create an experiment")
def create_an_experiment(experiment: ExperimentSaveDTO,
                         _=Depends(AuthService.check_user_access_token)) -> ExperimentDTO:
    """
    Create an experiment.
    """

    return ExperimentService.create_experiment_from_dto(
        experiment).to_dto()

###################################### UPDATE  ################################


@core_app.put("/experiment/{id_}/validate/{folder_id}", tags=["Experiment"], summary="Validate an experiment")
def validate_an_experiment(id_: str,
                           folder_id: str = None,
                           _=Depends(AuthService.check_user_access_token)) -> ExperimentDTO:
    """
    Validate a protocol

    - **id_**: the id_ of the experiment
    """

    return ExperimentService.validate_experiment_by_id(id_, folder_id=folder_id).to_dto()


@core_app.put("/experiment/{id_}/title", tags=["Experiment"],
              summary="Update the title of an experiment")
def update_title(id_: str,
                 body: dict,
                 _=Depends(AuthService.check_user_access_token)) -> ExperimentDTO:
    return ExperimentService.update_experiment_title(id_, body["title"]).to_dto()


class UpdateFolder(BaseModelDTO):
    folder_id: Optional[str]


@core_app.put("/experiment/{id_}/folder", tags=["Experiment"], summary="Update the folder of an experiment")
def update_experiment_folder(id_: str,
                             folder: UpdateFolder,
                             _=Depends(AuthService.check_user_access_token)) -> ExperimentDTO:
    """
    Update the folder of an experiment

    - **id_**: the id_ of the experiment
    - **folder_id**: the id_ of the folder
    """

    return ExperimentService.update_experiment_folder(id_, folder.folder_id).to_dto()


@core_app.put("/experiment/{id_}/description", tags=["Experiment"], summary="Update an experiment's description")
def update_experiment_description(id_: str,
                                  description: Dict,
                                  _=Depends(AuthService.check_user_access_token)) -> ExperimentDTO:
    """
    Update an experiment's description
    """

    return ExperimentService.update_experiment_description(id_, description).to_dto()


@core_app.put("/experiment/{id_}/reset", tags=["Experiment"], summary="Reset an experiment")
def reset_an_experiment(id_: str,
                        _=Depends(AuthService.check_user_access_token)) -> ExperimentDTO:
    return EntityNavigatorService.reset_experiment(id_).to_dto()


@core_app.get("/experiment/{id_}/reset/check-impact", tags=["Experiment"], summary="Check impact for experiment reset")
def check_impact_for_experiment_reset(id_: str,
                                      _=Depends(AuthService.check_user_access_token)) -> ImpactResultDTO:
    return EntityNavigatorService.check_impact_for_experiment_reset(id_).to_dto()


@core_app.put("/experiment/{id_}/sync-with-space", tags=["Experiment"],
              summary="Synchronise the experiment with the space")
def sync_with_space(id_: str,
                    _=Depends(AuthService.check_user_access_token)) -> ExperimentDTO:
    return ExperimentService.synchronize_with_space_by_id(id_).to_dto()

###################################### RUN ################################


@core_app.post("/experiment/{id_}/start", tags=["Experiment"], summary="Start an experiment")
def start_an_experiment(id_: str,
                        _=Depends(AuthService.check_user_access_token)) -> ExperimentDTO:
    """
    Start an experiment

    - **flow**: the flow object
    """

    return QueueService.add_experiment_to_queue(experiment_id=id_).to_dto()


@core_app.post("/experiment/{id_}/stop", tags=["Experiment"], summary="Stop an experiment")
def stop_an_experiment(id_: str,
                       _=Depends(AuthService.check_user_access_token)) -> ExperimentDTO:
    """
    Stop an experiment

    - **id_**: the experiment id_
    """

    return ExperimentRunService.stop_experiment(id_).to_dto()

################################### COPY ##############################


@core_app.put("/experiment/{id_}/clone", tags=["Experiment"], summary="Clone an experiment")
def clone_experiment(id_: str,
                     _=Depends(AuthService.check_user_access_token)) -> ExperimentDTO:
    return ExperimentService.clone_experiment(id_).to_dto()

################################### DELETE ##############################


@core_app.delete("/experiment/{id_}", tags=["Experiment"], summary="Delete an experiment")
def delete_experiment(id_: str,
                      _=Depends(AuthService.check_user_access_token)) -> None:
    return EntityNavigatorService.delete_experiment(id_)


################################### ARCHIVE ##############################
@core_app.put("/experiment/{id_}/archive", tags=["Experiment"], summary="Archive an experiment")
def archive(id_: str,
            _=Depends(AuthService.check_user_access_token)) -> ExperimentDTO:
    return ExperimentService.archive_experiment_by_id(id_).to_dto()


@core_app.put("/experiment/{id_}/unarchive", tags=["Experiment"], summary="Unarchive an experiment")
def unarchive(id_: str,
              _=Depends(AuthService.check_user_access_token)) -> ExperimentDTO:
    return ExperimentService.unarchive_experiment_by_id(id_).to_dto()


################################### INTERMEDIATE RESOURCES ##############################

@core_app.delete("/experiment/{id_}/intermediate-resources", tags=["Experiment"],
                 summary="Delete all intermediate resources of an experiment")
def delete_intermediate_resources(id_: str,
                                  _=Depends(AuthService.check_user_access_token)) -> None:
    return ExperimentService.delete_intermediate_resources(id_)

    ################################### CREATE EXPERIMENT FROM LINK ##############################


class ImportExpDto(BaseModelDTO):
    url: str
    mode: ExperimentDownloaderMode


@core_app.post("/experiment/import-from-lab", tags=["Share"],
               summary="Import an experiment from another lab")
def import_from_lab(import_dto: ImportExpDto,
                    _=Depends(AuthService.check_user_access_token)) -> ExperimentDTO:
    return ExperimentDownloaderService.import_from_lab(import_dto.url, import_dto.mode).to_dto()

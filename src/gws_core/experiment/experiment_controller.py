# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from typing import Dict, Optional

from fastapi import Depends
from git import List
from pydantic import BaseModel

from gws_core.core.classes.search_builder import SearchParams
from gws_core.core.model.model_dto import PageDTO

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


@core_app.get("/experiment/{id}", tags=["Experiment"], summary="Get an experiment")
def get_an_experiment(id: str,
                      _=Depends(AuthService.check_user_access_token)) -> ExperimentDTO:
    """
    Retrieve an experiment

    - **id**: the id of an experiment
    """

    return ExperimentService.get_experiment_by_id(id=id).to_dto()


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

    return ExperimentService.get_by_input_resource(
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


@core_app.put("/experiment/{id}/validate/{project_id}", tags=["Experiment"], summary="Validate an experiment")
def validate_an_experiment(id: str,
                           project_id: str = None,
                           _=Depends(AuthService.check_user_access_token)) -> ExperimentDTO:
    """
    Validate a protocol

    - **id**: the id of the experiment
    """

    return ExperimentService.validate_experiment_by_id(id=id, project_id=project_id).to_dto()


@core_app.put("/experiment/{id}", tags=["Experiment"], summary="Update an experiment")
def update_experiment(id: str,
                      experiment: ExperimentSaveDTO,
                      _=Depends(AuthService.check_user_access_token)) -> ExperimentDTO:
    """
    Update an experiment

    - **id**: the id of the experiment
    - **title**: the new title [optional]
    - **description**: the new description [optional]
    """

    return ExperimentService.update_experiment(id, experiment).to_dto()


@core_app.put("/experiment/{id}/title", tags=["Experiment"],
              summary="Update the title of an experiment")
def update_title(id: str,
                 body: dict,
                 _=Depends(AuthService.check_user_access_token)) -> ExperimentDTO:
    return ExperimentService.update_experiment_title(id, body["title"]).to_dto()


class UpdateProject(BaseModel):
    project_id: Optional[str]


@core_app.put("/experiment/{id}/project", tags=["Experiment"], summary="Update the project of an experiment")
def update_experiment_project(id: str,
                              project: UpdateProject,
                              _=Depends(AuthService.check_user_access_token)) -> ExperimentDTO:
    """
    Update the project of an experiment

    - **id**: the id of the experiment
    - **project_id**: the id of the project
    """

    return ExperimentService.update_experiment_project(id, project.project_id).to_dto()


@core_app.put("/experiment/{id}/description", tags=["Experiment"], summary="Update an experiment's description")
def update_experiment_description(id: str,
                                  description: Dict,
                                  _=Depends(AuthService.check_user_access_token)) -> ExperimentDTO:
    """
    Update an experiment's description
    """

    return ExperimentService.update_experiment_description(id, description).to_dto()


@core_app.put("/experiment/{id}/reset", tags=["Experiment"], summary="Reset an experiment")
def reset_an_experiment(id: str,
                        _=Depends(AuthService.check_user_access_token)) -> ExperimentDTO:
    return ExperimentService.reset_experiment(id).to_dto()


@core_app.put("/experiment/{id}/sync-with-space", tags=["Experiment"],
              summary="Synchronise the experiment with the space")
def sync_with_space(id: str,
                    _=Depends(AuthService.check_user_access_token)) -> ExperimentDTO:
    return ExperimentService.synchronize_with_space_by_id(id).to_dto()

###################################### RUN ################################


@core_app.post("/experiment/{id}/start", tags=["Experiment"], summary="Start an experiment")
def start_an_experiment(id: str,
                        _=Depends(AuthService.check_user_access_token)) -> ExperimentDTO:
    """
    Start an experiment

    - **flow**: the flow object
    """

    return QueueService.add_experiment_to_queue(experiment_id=id).to_dto()


@core_app.post("/experiment/{id}/stop", tags=["Experiment"], summary="Stop an experiment")
def stop_an_experiment(id: str,
                       _=Depends(AuthService.check_user_access_token)) -> ExperimentDTO:
    """
    Stop an experiment

    - **id**: the experiment id
    """

    return ExperimentRunService.stop_experiment(id=id).to_dto()

################################### COPY ##############################


@core_app.put("/experiment/{id}/clone", tags=["Experiment"], summary="Clone an experiment")
def clone_experiment(id: str,
                     _=Depends(AuthService.check_user_access_token)) -> ExperimentDTO:
    return ExperimentService.clone_experiment(id).to_dto()

################################### DELETE ##############################


@core_app.delete("/experiment/{id}", tags=["Experiment"], summary="Delete an experiment")
def delete_experiment(id: str,
                      _=Depends(AuthService.check_user_access_token)) -> None:
    ExperimentService.delete_experiment(id)


################################### ARCHIVE ##############################
@core_app.put("/experiment/{id}/archive", tags=["Experiment"], summary="Archive an experiment")
def archive(id: str,
            _=Depends(AuthService.check_user_access_token)) -> ExperimentDTO:
    return ExperimentService.archive_experiment_by_id(id).to_dto()


@core_app.put("/experiment/{id}/unarchive", tags=["Experiment"], summary="Unarchive an experiment")
def unarchive(id: str,
              _=Depends(AuthService.check_user_access_token)) -> ExperimentDTO:
    return ExperimentService.unarchive_experiment_by_id(id).to_dto()
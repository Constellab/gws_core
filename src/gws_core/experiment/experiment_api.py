# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, List, Optional

from fastapi import Depends
from gws_core.experiment.experiment import Experiment
from gws_core.study.study_dto import StudyDto
from gws_core.tag.tag import Tag
from gws_core.tag.tag_service import TagService

from ..core.classes.paginator import PaginatorDict
from ..core_app import core_app
from ..user.auth_service import AuthService
from ..user.user_dto import UserData
from .experiment_dto import ExperimentDTO
from .experiment_service import ExperimentService
from .queue_service import QueueService


###################################### GET ################################
@core_app.get("/experiment/{uri}", tags=["Experiment"], summary="Get an experiment")
def get_an_experiment(uri: str,
                      _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Retrieve an experiment

    - **uri**: the uri of an experiment
    """

    return ExperimentService.get_experiment_by_uri(uri=uri).to_json(deep=True)


@core_app.get("/experiment/queue", tags=["Experiment"], summary="Get the queue of experiment")
def get_the_experiment_queue(_: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Retrieve the queue of experiment
    """

    return QueueService.get_queue().to_json()


@core_app.get("/experiment", tags=["Experiment"], summary="Get the list of experiments")
def get_the_list_of_experiments(page: Optional[int] = 1,
                                number_of_items_per_page: Optional[int] = 20,
                                _: UserData = Depends(AuthService.check_user_access_token)) -> PaginatorDict:
    """
    Retrieve a list of experiments. The list is paginated.

    - **search_text**: text used to filter the results. The text is matched against to the `title` and the `description` using full-text search.
    - **page**: the page number
    - **number_of_items_per_page**: the number of items per page (limited to 50)
    """

    return ExperimentService.fetch_experiment_list(
        page=page,
        number_of_items_per_page=number_of_items_per_page,
    ).to_json()


###################################### CREATE ################################

@core_app.post("/experiment", tags=["Experiment"], summary="Create an experiment")
def create_an_experiment(experiment: ExperimentDTO,
                         _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Create an experiment.

    - **study_uri**: the uri of the study
    - **title**: the title of the experiment [optional]
    - **description**: the description of the experiment [optional]
    """

    return ExperimentService.create_empty_experiment(
        experiment).to_json(deep=True)

###################################### UPDATE  ################################


@core_app.put("/experiment/{uri}/validate", tags=["Experiment"], summary="Validate an experiment")
def validate_an_experiment(uri: str,
                           study_dto: Optional[StudyDto] = None,
                           _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Validate a protocol

    - **uri**: the uri of the experiment
    """

    return ExperimentService.validate_experiment_send_to_central(uri=uri, study_dto=study_dto).to_json(deep=True)


@core_app.put("/experiment/{uri}/protocol", tags=["Experiment"], summary="Update an experiment's protocol")
def update_experiment_protocol(uri: str,
                               protocol_graph: Dict,
                               _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Update an experiment

    - **protocol_graph**: the new protocol graph
    """

    return ExperimentService.update_experiment_protocol(uri, protocol_graph).to_json(deep=True)


@core_app.put("/experiment/{uri}", tags=["Experiment"], summary="Update an experiment")
def update_experiment(uri: str,
                      experiment: ExperimentDTO,
                      _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Update an experiment

    - **uri**: the uri of the experiment
    - **title**: the new title [optional]
    - **description**: the new description [optional]
    """

    return ExperimentService.update_experiment(uri, experiment).to_json(deep=True)


###################################### RUN ################################

@core_app.post("/experiment/{uri}/start", tags=["Experiment"], summary="Start an experiment")
def start_an_experiment(uri: str,
                        _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Start an experiment

    - **flow**: the flow object
    """

    return QueueService.add_experiment_to_queue(experiment_uri=uri).to_json()


@core_app.post("/experiment/{uri}/stop", tags=["Experiment"], summary="Stop an experiment")
def stop_an_experiment(uri: str,
                       _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Stop an experiment

    - **uri**: the experiment uri
    """

    return ExperimentService.stop_experiment(uri=uri).to_json(deep=True)

###################################### RUN ################################


@core_app.put("/experiment/{uri}/tags", tags=["Experiment"], summary="Update experiment tags")
def stop_an_experiment(uri: str,
                       tags: List[Tag],
                       _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    return TagService.save_tags_to_model(Experiment._typing_name, uri, tags)

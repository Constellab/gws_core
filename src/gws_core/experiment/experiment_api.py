# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Optional

from fastapi import Depends

from ..core.classes.paginator import Paginator
from ..core_app import core_app
from ..model.model_service import ModelService
from ..user.auth_service import AuthService
from ..user.user_dto import UserData
from .experiment import Experiment
from .experiment_dto import ExperimentDTO
from .experiment_service import ExperimentService
from .queue_service import QueueService


@core_app.get("/experiment/queue", tags=["Experiment"], summary="Get the queue of experiment")
async def get_the_experiment_queue(_: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Retrieve the queue of experiment
    """

    q = QueueService.get_queue()
    return q.to_json()


@core_app.post("/experiment/{uri}/start", tags=["Experiment"], summary="Start an experiment")
async def start_an_experiment(uri: str,
                              _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Start an experiment

    - **flow**: the flow object
    """

    e = await QueueService.add_experiment_to_queue(experiment_uri=uri)
    return e.to_json()


@core_app.post("/experiment/{uri}/stop", tags=["Experiment"], summary="Stop an experiment")
async def stop_an_experiment(uri: str,
                             _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Stop an experiment

    - **uri**: the experiment uri
    """

    e = await ExperimentService.stop_experiment(uri=uri)
    return e.to_json()


@core_app.post("/experiment/{uri}/archive", tags=["Experiment"], summary="Archive an experiment")
async def archive_an_experiment(uri: str,
                                _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Archive an experiment

    - **uri**: the uri of the experiment
    """

    e = ModelService.archive_model(object_type="experiment", object_uri=uri)
    return e.to_json()


@core_app.post("/experiment/{uri}/unarchive", tags=["Experiment"], summary="Unarchive an experiment")
async def unarchive_an_experiment(uri: str,
                                  _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Unarchive an experiment

    - **uri**: the uri of the experiment
    """

    e = ModelService.unarchive_model(object_type="experiment", object_uri=uri)
    return e.to_json()


@core_app.post("/experiment/{uri}/validate", tags=["Experiment"], summary="Validate an experiment")
async def validate_an_experiment(uri: str,
                                 _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Validate a protocol

    - **uri**: the uri of the experiment
    """

    e = ExperimentService.validate_experiment(uri=uri)
    return e.to_json()


@core_app.get("/experiment/{uri}", tags=["Experiment"], summary="Get an experiment")
async def get_an_experiment(uri: str,
                            _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Retrieve an experiment

    - **uri**: the uri of an experiment
    """

    e = ExperimentService.fetch_experiment(uri=uri)
    return e.to_json()


@core_app.put("/experiment/{uri}", tags=["Experiment"], summary="Update an experiment")
async def update_an_experiment(uri: str,
                               experiment: ExperimentDTO,
                               _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Update an experiment

    - **uri**: the uri of the experiment
    - **title**: the new title [optional]
    - **description**: the new description [optional]
    - **flow**: the new protocol flow [optional]
    """

    expeirment = ExperimentService.update_experiment(uri, experiment)
    return expeirment.to_json()


@core_app.post("/experiment", tags=["Experiment"], summary="Create an experiment")
async def create_an_experiment(experiment: ExperimentDTO,
                               _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Create an experiment.

    - **study_uri**: the uri of the study
    - **title**: the title of the experiment [optional]
    - **description**: the description of the experiment [optional]
    - **flow**: the protocol flow [optional]
    """

    experiment: Experiment = ExperimentService.create_experiment(experiment)
    return experiment.to_json()


@core_app.get("/experiment", tags=["Experiment"], summary="Get the list of experiments")
async def get_the_list_of_experiments(page: Optional[int] = 1,
                                      number_of_items_per_page: Optional[int] = 20,
                                      _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Retrieve a list of experiments. The list is paginated.

    - **search_text**: text used to filter the results. The text is matched against to the `title` and the `description` using full-text search.
    - **page**: the page number
    - **number_of_items_per_page**: the number of items per page (limited to 50)
    """

    experiments: Paginator = ExperimentService.fetch_experiment_list(
        page=page,
        number_of_items_per_page=number_of_items_per_page,
    )

    return experiments.to_json(shallow=True)

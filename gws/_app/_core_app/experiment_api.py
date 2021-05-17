# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws.service.experiment_service import ExperimentService
from gws.dto.experiment_dto import ExperimentDTO
from typing import Dict, Optional
from fastapi import Depends

from gws.http import *
from ._auth_user import UserData, check_user_access_token
from .core_app import core_app

@core_app.get("/experiment/queue", tags=["Experiment"], summary="Get the queue of experiment")
async def get_experiment_queue() -> (dict, str,):
    """
    Retrieve the queue of experiment
    """

    return ExperimentService.get_queue()
    
@core_app.get("/experiment/list", tags=["Experiment"], summary="Get the list of experiments")
async def get_list_of_experiments(page: int = 1, \
                                  number_of_items_per_page: int = 20, \
                                  _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Retrieve a list of experiments. The list is paginated.

    - **page**: the page number
    - **number_of_items_per_page**: the number of items per page (limited to 50) 
    """
    
    return ExperimentService.fetch_experiment_list(
        page = page, 
        number_of_items_per_page = number_of_items_per_page
    )

@core_app.post("/experiment/{uri}/start", tags=["Experiment"], summary="Start an experiment")
async def start_experiment(uri: str, \
                         _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Start an experiment
    
    - **flow**: the flow object 
    """
    
    return await ExperimentService.start_experiment(uri=uri)

@core_app.post("/experiment/{uri}/stop", tags=["Experiment"], summary="Stop a running experiment")
async def stop_experiment(uri: str, \
                         _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Stop an experiment
    
    - **uri**: the experiment uri
    """

    from gws.service.experiment_service import ExperimentService
    return await ExperimentService.stop_experiment(uri=uri)


@core_app.put("/experiment/{uri}", tags=["Experiment"], summary="Update an experiment")
async def update_experiment(uri: str,
                            experiment: ExperimentDTO,
                            _: UserData = Depends(check_user_access_token)) -> Dict:
    """
    Update an experiment

    - **uri**: the uri of the experiment
    - **title**: the new title [optional]
    - **description**: the new description [optional]
    - **flow**: the new protocol flow [optional]
    """

    return ExperimentService.update_experiment(uri, experiment)

@core_app.post("/experiment/{uri}/archive", tags=["Experiment"])
async def archive_experiment(uri:str, \
                             _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Archive an experiment
    
    - **uri**: the uri of the experiment
    """
    
    from gws.service.model_service import ModelService
    return ModelService.archive_model(object_type="experiment", object_uri=uri)

@core_app.post("/experiment/{uri}/unarchive", tags=["Experiment"])
async def unarchive_experiment(uri:str, \
                               _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Unarchive an experiment
    
    - **uri**: the uri of the experiment
    """
    
    from gws.service.model_service import ModelService
    return ModelService.unarchive_model(object_type="experiment", object_uri=uri)
    
@core_app.post("/experiment/{uri}/validate", tags=["Experiment"], summary="Validate an experiment")
async def validate_experiment(uri: str, \
                              _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Validate a protocol
    
    - **uri**: the uri of the experiment
    """
    
    from gws.service.experiment_service import ExperimentService
    return ExperimentService.validate_experiment(uri=uri)

@core_app.post("/experiment", tags=["Experiment"], summary="Create an experiment")
async def create_experiment(experiment: ExperimentDTO,
                            _: UserData = Depends(check_user_access_token)) -> Dict:
    """
    Create an experiment.

    - **study_uri**: the uri of the study
    - **title**: the title of the experiment [optional]
    - **description**: the description of the experiment [optional]
    - **flow**: the protocol flow [optional]
    """

    return ExperimentService.create_experiment(experiment)

@core_app.get("/experiment/{uri}", tags=["Experiment"], summary="Get an experiment")
async def get_experiment(uri: str, \
                       _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Retrieve an experiment
    
    - **uri**: the uri of an experiment
    """
    
    return ExperimentService.fetch_experiment(uri=uri)

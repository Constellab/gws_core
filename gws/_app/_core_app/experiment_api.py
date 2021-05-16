# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Optional
from fastapi import Depends

from gws.http import *
from ._auth_user import UserData, check_user_access_token
from .core_app import core_app

@core_app.get("/experiment/queue", tags=["Experiment"], summary="Get the queue of experiment")
async def get_experiment_queue() -> (dict, str,):
    """
    Retrieve the queue of experiment
    """

    from gws.service.experiment_service import ExperimentService
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
    
    from gws.service.experiment_service import ExperimentService
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
    
    from gws.service.experiment_service import ExperimentService
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


@core_app.post("/experiment/{uri}/update", tags=["Experiment"], summary="Update an experiment")
async def update_experiment(uri:str, \
                            title: Optional[str] = None,\
                            description: Optional[str] = None,\
                            flow: Optional[dict] = None, \
                            _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Update an experiment
    
    - **uri**: the uri of the experiment
    - **title**: the new title [optional]
    - **description**: the new description [optional]
    - **flow**: the new protocol flow [optional]
    """
    
    from gws.service.experiment_service import ExperimentService
    return ExperimentService.update_experiment(
        uri = uri, 
        title = title, 
        description = description, 
        data = flow
    )

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

@core_app.put("/experiment/{uri}/create", tags=["Experiment"], summary="Create an experiment")
async def create_experiment(study_uri:str, \
                            uri: Optional[str]=None, \
                            title: Optional[str]=None, \
                            description: Optional[str]=None, \
                            proto: Optional[dict]=None, \
                            _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Create an experiment.
    
    - **study_uri**: the uri of the study
    - **uri**: predifined experiment uri [optional]
    - **title**: the title of the experiment [optional]
    - **description**: the description of the experiment [optional]
    - **flow**: the protocol flow [optional]
    """
    
    from gws.service.experiment_service import ExperimentService
    return ExperimentService.create_experiment(
        study_uri = study_uri,
        uri = uri,
        title = title, 
        description = description, 
        data = flow
    )

@core_app.get("/experiment/{uri}", tags=["Experiment"], summary="Get an experiment")
async def get_experiment(uri: str, \
                       _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Retrieve an experiment
    
    - **uri**: the uri of an experiment
    """
    
    from gws.service.experiment_service import ExperimentService
    return ExperimentService.fetch_experiment(uri=uri)
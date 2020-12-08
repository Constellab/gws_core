# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Optional

from fastapi import Depends, FastAPI
from fastapi.responses import Response, RedirectResponse
from pydantic import BaseModel

from gws.settings import Settings
from gws.central import Central
from gws.controller import Controller
from gws.model import Model, ViewModel, Experiment

core_app = FastAPI(docs_url="/apidocs")

class _ViewModel(BaseModel):
    uri: str
    data: dict

# ##################################################################
#
# List
#
# ##################################################################

@core_app.get("/experiment/list", tags=["Object list"], summary="Get the list of experiments")
async def get_list_of_experiments(page: int = 1, number_of_items_per_page: int = 20) -> (dict, str,):
    """
    Retrieve a list of experiments. The list is paginated.

    - **page**: the page number 
    - **number_of_items_per_page**: the number of items per page (limited to 50) 
    """

    return Controller.fetch_experiment_list(
        page=page, 
        number_of_items_per_page=number_of_items_per_page,
        return_format="json"
    )

@core_app.get("/job/list", tags=["Object list"], summary="Get the list of jobs")
async def get_list_of_jobs(experiment_uri: str = None, page: int = 1, number_of_items_per_page: int = 20) -> (dict, str,):
    """
    Retrieve a list of jobs. The list is paginated.

    - **experiment_uri**: the uri of the experiment in which the jobs were run
    - **page**: the page number 
    - **number_of_items_per_page**: the number of items per page (limited to 50) 
    """

    return Controller.fetch_job_list(
        page=page, 
        number_of_items_per_page=number_of_items_per_page,
        experiment_uri=experiment_uri, 
        return_format="json"
    )

@core_app.get("/protocol/list", tags=["Object list"], summary="Get the list of protocols")
async def get_list_of_protocols(job_uri: str = None, page: int = 1, number_of_items_per_page: int = 20) -> (dict, str,):
    """
    Retrieve a list of protocols. The list is paginated.

    - **job_uri**: the uri of job related the protocol (only one procotol is related to given job)
    - **page**: the page number 
    - **number_of_items_per_page**: the number of items per page (limited to 50 if job_uri is not given) 
    """

    return Controller.fetch_protocol_list(
        page=page, 
        number_of_items_per_page=number_of_items_per_page,
        job_uri=job_uri, 
        return_format="json"
    )

@core_app.get("/process/list", tags=["Object list"], summary="Get the list of processes")
async def get_list_of_process(job_uri: str = None, page: int = 1, number_of_items_per_page: int = 20) -> (dict, str,):
    """
    Retrieve a list of processes. The list is paginated.

    - **job_uri**: the uri of job related the process (only one process is related to given job)
    - **page**: the page number 
    - **number_of_items_per_page**: the number of items per page (limited to 50 if job_uri is not given) 
    """

    return Controller.fetch_process_list(
        page=page, 
        number_of_items_per_page=number_of_items_per_page,
        job_uri=job_uri, 
        return_format="json"
    )

@core_app.get("/config/list", tags=["Object list"], summary="Get the list of configs")
async def get_list_of_configs(job_uri: str = None, page: int = 1, number_of_items_per_page: int = 20) -> (dict, str,):
    """
    Retrieve a list of configs. The list is paginated.

    - **job_uri**: the uri of job related the config (only one config is related to given job)
    - **page**: the page number 
    - **number_of_items_per_page**: the number of items per page (limited to 50 if job_uri is not given) 
    """

    return Controller.fetch_config_list(
        page=page, 
        number_of_items_per_page=number_of_items_per_page,
        job_uri=job_uri, 
        return_format="json"
    )

@core_app.get("/resource/list", tags=["Object list"], summary="Get the list of resources")
async def get_list_of_resources(job_uri: str = None, experiment_uri: str = None, page: int = 1, number_of_items_per_page: int = 20) -> (dict, str,):
    """
    Retrieve a list of resources. The list is paginated.

    - **job_uri**: the uri of the job in which the resource was generated
    - **experiment_uri**: the uri of the exepriment in which the resource was generated (will be ignored if job_uri is provided)
    - **page**: the page number 
    - **number_of_items_per_page**: the number of items per page (limited to 50 if job_uri or experiment_uri are not given) 
    """

    return Controller.fetch_resource_list(
        page=page, 
        number_of_items_per_page=number_of_items_per_page, 
        experiment_uri=experiment_uri, 
        job_uri=job_uri, return_format="json"
    )


@core_app.post("/run/{experiment_uri}", tags=["Run"])
async def run_experiment(experiment_uri: str) -> (dict, str,):
    """
    Run an experiment
    """

    return await Controller.action(action="run", object_uri=experiment_uri)

# ##################################################################
#
# Get, Post, Put, Delete
#
# ##################################################################

@core_app.post("/", tags=["Generic CRUD operations on objects"])
async def post_view_model(object_type: str, vmodel: _ViewModel) -> (dict, str,):
    """
    Post an render a ViewModel
    """

    return Controller.action(action="post", object_type=object_type, object_uri=vmodel.uri, data=vmodel.data, return_format="json")

@core_app.put("/{object_type}/", tags=["Generic CRUD operations on objects"])
async def put_view_model(object_type: str, vmodel: _ViewModel) -> (dict, str,):
    """
    Post and render a ViewModel
    """

    return Controller.action(action="put", object_type=object_type, object_uri=vmodel.uri, data=vmodel.data, return_format="json")


@core_app.get("/{object_type}/{object_uri}", tags=["Generic CRUD operations on objects"])
async def get_model_or_viewmodel(object_type: str, object_uri: str) -> (dict, str,):
    """
    Get and render a ViewModel
    """

    return Controller.action(action="get", object_type=object_type, object_uri=object_uri, return_format="json")

@core_app.delete("/{object_type}/{object_uri}/", tags=["Generic CRUD operations on objects"])
async def delete_view_model(object_type: str, object_uri: str) -> (dict, str,):
    """
    Post a ViewModel and render its
    """

    return Controller.action(action="delete", object_type=object_type, object_uri=object_uri)

# ##################################################################
#
# Robot
#
# ##################################################################

@core_app.post("/run-robot-travel-experiment", tags=["Astro boy travels"])
async def run_robot_travel_experiment() -> (dict, str,):
    """
    Run robot experiments
    """

    return await Controller._run_robot_travel()

@core_app.post("/run-robot-super-travel-experiment", tags=["Astro boy travels"])
async def run_robot_super_travel_experiment() -> (dict, str,):
    """
    Run robot experiments
    """

    return await Controller._run_robot_super_travel()
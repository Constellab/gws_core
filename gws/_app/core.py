# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
from typing import Optional, List

from fastapi import Depends, FastAPI, UploadFile, Request, File as FastAPIFile
from fastapi.responses import Response, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware


from pydantic import BaseModel

from gws.settings import Settings
from gws.central import Central
from gws.controller import Controller
from gws.model import Model, ViewModel, Experiment

core_app = FastAPI(docs_url="/apidocs")

# Enable core for the API
core_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET,HEAD,PUT,PATCH,POST,DELETE"],
    allow_headers=["Origin,X-Requested-With,Content-Type,Accept,Authorization,authorization,X-Forwarded-for,lang"],
)

class _ViewModel(BaseModel):
    uri: str
    data: dict

        
# ##################################################################
#
# List
#
# ##################################################################

@core_app.get("/experiment/list", tags=["CRUD operations on experiments"], summary="Get the list of experiments")
async def get_list_of_experiments(page: int = 1, number_of_items_per_page: int = 20) -> (dict, str,):
    """
    Retrieve a list of experiments. The list is paginated.

    - **page**: the page number 
    - **number_of_items_per_page**: the number of items per page (limited to 50) 
    """

    return Controller.fetch_experiment_list(
        page=page, 
        number_of_items_per_page=number_of_items_per_page
    )

@core_app.post("/experiment/save/", tags=["CRUD operations on experiments"], summary="Save an experiment")
async def save_experiment(experiment_uri: str, flow: Optional[dict]) -> (dict, str,):
    """
    Save an experiment
    """

    return await Controller.save_experiment(object_uri=experiment_uri, data=flow)


@core_app.post("/experiment/run/", tags=["CRUD operations on experiments"], summary="Run and experiment")
async def run_experiment(experiment_uri: str) -> (dict, str,):
    """
    Run an experiment
    """

    return await Controller.run_experiment(object_uri=experiment_uri)

@core_app.get("/job/flow", tags=["CRUD operations on experiments"], summary="Get jobs' flows")
async def get_jobs_flow(protocol_job_uri: str = None, experiment_uri: str = None) -> (dict, str,):
    """
    Retrieve the jobs' flow of an experiment or a protocol job
    
    - **protocol_job_uri**: the uri of the job (must be a job of a protocol)
    - **experiment_uri**: the uri of an experiment (is not used if job_uri is given)
    """

    return Controller.fetch_job_flow(protocol_job_uri=protocol_job_uri, experiment_uri=experiment_uri)

@core_app.get("/job/list", tags=["CRUD operations on experiments"], summary="Get the list of jobs")
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
        experiment_uri=experiment_uri
    )

@core_app.get("/protocol/list", tags=["CRUD operations on experiments"], summary="Get the list of protocols")
async def get_list_of_protocols(experiment_uri: str = None, job_uri: str = None, page: int = 1, number_of_items_per_page: int = 20) -> (dict, str,):
    """
    Retrieve a list of protocols. The list is paginated.
    
    - **experiment_uri**: the uri of experiment related to the protocol (an experiment is related to one protocol). If given, the job_uri is not used.
    - **job_uri**: the uri of job related to the protocol (a job is related to one protocol)
    - **page**: the page number 
    - **number_of_items_per_page**: the number of items per page (limited to 50 if job_uri nor experiment_uri are not given) 
    """

    return Controller.fetch_protocol_list(
        page=page, 
        number_of_items_per_page=number_of_items_per_page,
        experiment_uri=experiment_uri,
        job_uri=job_uri
    )

@core_app.get("/process/list", tags=["CRUD operations on experiments"], summary="Get the list of processes")
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
        job_uri=job_uri
    )

@core_app.get("/config/list", tags=["CRUD operations on experiments"], summary="Get the list of configs")
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
        job_uri=job_uri
    )

@core_app.get("/resource/list", tags=["CRUD operations on experiments"], summary="Get the list of resources")
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
        job_uri=job_uri
    )

# ##################################################################
#
# Get, Post, Put, Delete
#
# ##################################################################

@core_app.get("/count/{object_type}/", tags=["Generic CRUD operations on object views"])
async def count(object_type: str) -> (dict, str,):
    """
    Update a view model
    """

    return await Controller.action(action="count", object_type=object_type)

@core_app.get("/view/{object_type}/{object_uris}/", tags=["Generic CRUD operations on object views"])
async def get_view_model(object_type: str, object_uris: Optional[str] = "all", \
                        page: int = 1, number_of_items_per_page: int = 20, \
                        filters: Optional[str] = "{}", view_params: Optional[str] = "{}") -> (dict, str,):
    """
    Get a view model.
    
    Custom query params depending on the queryied model. 
    
    - **object_type**: the type of the object to fetch
    - **object_uris**: the uris of the object to fetch. Use comma-separated values to fecth several uris or 'all' to fetch all the entries. When all entries are retrieve, the **filter** parameter can be used.
    - **page**: the page number 
    - **number_of_items_per_page**: the number of items per page (limited to 50 if **job_uri** or **experiment_uri** are not given) 
    - **filters**: filter to use to select data (**object_uris** must be equal to 'all'). The filter is matches using full-text search against to the `title` and the `description`. The format is `filter={"title": "Searched title*", "description": "This is a description for full-text search"}`
    - **view_params**: key,value parameters of the view model. The key,value specifications are given by the method `as_json()` of the corresponding object class. See class documentation.
    """
    
    try:
        params = json.loads(view_params)
    except:
        params = {}
        
    return await Controller.action(
        action="get", object_type=object_type, object_uri=object_uris, data=params, 
        page=page, number_of_items_per_page=number_of_items_per_page, 
        filters=filters
    )

@core_app.put("/view/{object_type}/", tags=["Generic CRUD operations on object views"])
async def update_view_model(object_type: str, view_model: _ViewModel) -> (dict, str,):
    """
    Update a view model
    """

    return await Controller.action(action="put", object_type=object_type, object_uri=view_model.uri, data=view_model.data)

@core_app.delete("/view/{object_type}/{object_uri}/", tags=["Generic CRUD operations on object views"])
async def delete_view_model(object_type: str, object_uri: str) -> (dict, str,):
    """
    Delete a view model
    
    - **object_type**: the type of the object to fetch
    - **object_uri**: the uri of the objects to fetch
    """

    return await Controller.action(action="delete", object_type=object_type, object_uri=object_uri)

# ##################################################################
#
# IO File
#
# ##################################################################


@core_app.post("/upload", tags=["Upload and download files"])
async def upload(files: List[UploadFile] = FastAPIFile(...)):
    """
    Upload files
    """
          
    return await Controller.action(action="upload", data=files)

@core_app.post("/download/{file_uri}", tags=["Upload and download files"])
async def download(file_uri: str):
    """
    Download file
    """
          
    return {"status": False, "message": "Not yet available"}
      

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
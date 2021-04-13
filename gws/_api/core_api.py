# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import importlib
import json

from typing import Optional, List

from fastapi import Depends, FastAPI, \
                    UploadFile, Request, \
                    HTTPException, File as FastAPIFile
from fastapi.responses import Response, JSONResponse, RedirectResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette_context import context
from starlette_context.middleware import ContextMiddleware

from pydantic import BaseModel

from gws.settings import Settings
from gws.central import Central
from gws.controller import Controller
from gws.model import Model, ViewModel, Experiment
from gws.http import *

from ._auth_user import UserData, \
                        OAuth2UserTokenRequestForm, \
                        check_user_access_token

from ._auth_central import check_central_api_key

app = FastAPI(docs_url="/docs")

# Enable core for the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    ContextMiddleware
)

class ViewModelData(BaseModel):
    uri: str
    params: dict

class ProcessData(BaseModel):
    uri:str
    type:str = "gws.model.Process"
    title:str = None
    instance_name: str
    config_specs: dict = {}
    input_specs: dict = {}
    output_specs: dict = {}

class ConfigData(BaseModel):
    uri:str = None
    type:str = "gws.model.Config"
    params: dict = {}
    
class ProtocolData(ProcessData):
    type: str = "gws.model.Protocol"
    interfaces: dict = {}
    outerfaces: dict = {}
    
    
# ##################################################################
#
# List
#
# ##################################################################

@app.get("/experiment/list", tags=["Experiment"], summary="Get the list of experiments")
async def get_list_of_experiments(page: int = 1, number_of_items_per_page: int = 20, \
                                  _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Retrieve a list of experiments. The list is paginated.

    - **page**: the page number 
    - **number_of_items_per_page**: the number of items per page (limited to 50) 
    """

    return Controller.fetch_experiment_list(
        page=page, 
        number_of_items_per_page=number_of_items_per_page
    )

@app.post("/experiment/save", tags=["Experiment"], summary="Save an experiment using a flow")
async def save_experiment(flow: Optional[dict], \
                          _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Save a protocol.
    
    - **flow**: the flow object 
    """
    
    return Controller.save_experiment(data=flow)

@app.post("/experiment/run/", tags=["Experiment"], summary="Run an experiment")
async def run_experiment(flow: Optional[dict], \
                         _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Run an experiment
    
    - **flow**: the flow object 
    """

    return await Controller.run_experiment(data=flow)

@app.post("/experiment/validate/", tags=["Experiment"], summary="Validate an experiment")
async def validate_experiment(uri: str = None, \
                              _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Validate an experiment
    
    - **uri**: the experiment uri
    """

    return Controller.validate_experiment(uri=uri)

@app.get("/experiment/", tags=["Experiment"], summary="Get experiment flow")
async def get_experiment(experiment_uri: str = None, \
                       _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Retrieve the job flow of an experiment or a protocol job
    
    - **protocol_job_uri**: the uri of the job (must be a job of a protocol)
    - **experiment_uri**: the uri of an experiment (is not used if job_uri is given)
    """

    return Controller.fetch_experiment(experiment_uri=experiment_uri)


@app.get("/protocol/list", tags=["Experiment"], summary="Get the list of protocols")
async def get_list_of_protocols(experiment_uri: str = None, job_uri: str = None, \
                                page: int = 1, number_of_items_per_page: int = 20, \
                                _: UserData = Depends(check_user_access_token)) -> (dict, str,):
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

@app.post("/protocol/validate/", tags=["Experiment"], summary="Validate an experiment")
async def validate_experiment(uri: str = None, \
                              _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Validate a protocol
    
    - **uri**: the protocol uri
    """

    return Controller.validate_protocol(uri=uri)

@app.get("/process-type/list", tags=["Experiment"], summary="Get the list of process types")
async def get_list_of_process_types(page: int = 1, number_of_items_per_page: int = 20, \
                              _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Retrieve a list of processes. The list is paginated.

    - **job_uri**: the uri of job related the process (only one process is related to given job)
    - **page**: the page number 
    - **number_of_items_per_page**: the number of items per page (limited to 50 if job_uri is not given) 
    """

    return Controller.fetch_process_type_list(
        page=page, 
        number_of_items_per_page=number_of_items_per_page,
        job_uri=job_uri
    )

@app.get("/process/list", tags=["Experiment"], summary="Get the list of processes")
async def get_list_of_process(experiment_uri: str = None, \
                              page: int = 1, number_of_items_per_page: int = 20, \
                              _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Retrieve a list of processes. The list is paginated.

    - **job_uri**: the uri of job related the process (only one process is related to given job)
    - **page**: the page number 
    - **number_of_items_per_page**: the number of items per page (limited to 50 if job_uri is not given) 
    """

    return Controller.fetch_process_list(
        page=page, 
        number_of_items_per_page=number_of_items_per_page,
        experiment_uri=experiment_uri
    )

@app.get("/config/list", tags=["Experiment"], summary="Get the list of configs")
async def get_list_of_configs(experiment_uri: str = None, \
                              page: int = 1, number_of_items_per_page: int = 20, \
                              _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Retrieve a list of configs. The list is paginated.

    - **job_uri**: the uri of job related the config (only one config is related to given job)
    - **page**: the page number 
    - **number_of_items_per_page**: the number of items per page (limited to 50 if job_uri is not given) 
    """

    return Controller.fetch_config_list(
        page=page, 
        number_of_items_per_page=number_of_items_per_page,
        experiment_uri=experiment_uri
    )

@app.get("/resource/list", tags=["Experiment"], summary="Get the list of resources")
async def get_list_of_resources(experiment_uri: str = None, page: int = 1, number_of_items_per_page: int = 20, \
                                _: UserData = Depends(check_user_access_token)) -> (dict, str,):
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
        experiment_uri=experiment_uri
    )

# ##################################################################
#
# Get, Post, Put, Delete, Verify
#
# ##################################################################

@app.get("/count/{object_type}/", tags=["Generic models and view models"])
async def count(object_type: str, \
                _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Get the count of objects of a given type
    
    - **object_type**: the object type
    """

    return await Controller.action(action="count", object_type=object_type)

@app.get("/view/{object_type}/{object_uris}/", tags=["Generic models and view models"])
async def get_view_model(object_type: str, object_uris: Optional[str] = "all", \
                        page: int = 1, number_of_items_per_page: int = 20, \
                        filters: Optional[str] = "{}", view_params: Optional[str] = "{}", \
                        _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Get a ViewModel
    
    Custom query params depending on the queryied model. 
    
    - **object_type**: the type of the object to fetch. Can be an existing ViewModel or a Viewable object with no ViewModel. In this case, default ViewModel is created and returned.
    - **object_uris**: the uris of the object to fetch. Use comma-separated values to fecth several uris or 'all' to fetch all the entries. When all entries are retrieve, the **filter** parameter can be used.
    - **page**: the page number 
    - **number_of_items_per_page**: the number of items per page (limited to 50 if **job_uri** or **experiment_uri** are not given) 
    - **filters**: filter to use to select data (**object_uris** must be equal to 'all'). The filter is matches using full-text search against to the `title` and the `description`. The format is `filter={"title": "Searched title*", "description": "This is a description for full-text search"}`
    - **view_params**: key,value parameters of the ViewModel. The key,value specifications are given by the method `as_json()` of the corresponding object class. See class documentation.
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

@app.put("/view/{object_type}/", tags=["Generic models and view models"])
async def update_view_model(object_type: str, view_model: ViewModelData, \
                            _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Update a ViewModel
    
    - **object_type**: the type of object of which the ViewModel is attached
    - **view_model**: data of the ViewModel `{uri: "uri_of_the_view_model", data: "parameters_of_the_view_model"}`
    """

    return await Controller.action(action="update", object_type=object_type, object_uri=view_model.uri, data=view_model.params)

@app.delete("/view/{object_type}/{object_uri}/", tags=["Generic models and view models"])
async def delete_view_model(object_type: str, object_uri: str, \
                            _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Delete a ViewModel
    
    - **object_type**: the type of the object to delete.
    - **object_uri**: the uri of the object to delete
    """

    return await Controller.action(action="delete", object_type=object_type, object_uri=object_uri)

@app.get("/verify/{object_type}/{object_uri}/", tags=["Generic models and view models"])
async def verify(object_type: str, object_uri: str, \
                _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Block-chain like verification of object integrity.
    
    Verify the integrity of a given object in the db to check if that object has been altered by any unofficial mean
    (e.g. manual changes of data in db, or partial changes without taking care of its dependency chain).
    
    Objects' integrity is based on an algorithm that compute hashes using objects' data and their dependency trees.
    
    - **object_type**: the type of the object to delete.
    - **object_uri**: the uri of the object to delete
    """

    return await Controller.verify(action="verify", object_type=object_type, object_uri=object_uri)

# ##################################################################
#
# IO File
#
# ##################################################################

@app.api_route("/brick/{brick_name}/{api_func}", response_class=JSONResponse, methods=["GET", "POST"], tags=["User bricks"])
async def call_brick_api(request: Request, \
                         brick_name: Optional[str] = "gws", api_func: Optional[str] = None, \
                         _: UserData = Depends(check_user_access_token)) :
    """
    Call a custom api function of a brick
    
    - **brick_name**: the name of the brick
    - **api_func**: the target api function. 
    
    For example of **brick_name=foo** and **api_func=do-thing**, the method **foo.app.API.do_thing( request: fastapi.requests.Request )** with be called if it exists. The current **request** will be passed to the function. The function
    **do_thing** should return a JSON response as a dictionnary.
    """
    
    try:
        brick_app_module = importlib.import_module(f"{brick_name}.app")
        api_t = getattr(brick_app_module, "API", None)
        if api_t is None:
            raise Error("call_brick_api", f"Class {brick_name}.app.API not found")
            
        api_func = api_func.replace("-","_").lower()
        async_func = getattr(api_t, api_func, None)
        if async_func is None:
            raise Error("call_brick_api", f"Method {brick_name}.app.API.{api_func} not found")
        else:
            return await async_func(request)
    
    except Error as err:
        raise HTTPInternalServerError(detail=str(err))
        
    except Exception as err:
        Logger.error(f"{err}")
        raise HTTPInternalServerError(detail=str(err))
        
    except HTTPError as err:
        message = f"HTTPError: status_code = {err.status_code}, detail = {err.detail}"
        Logger.error(message)
        raise err
        
# ##################################################################
#
# IO File
#
# ##################################################################


@app.post("/upload", tags=["Upload and download files"])
async def upload(files: List[UploadFile] = FastAPIFile(...), study_uri:Optional[str] = None, \
                 _: UserData = Depends(check_user_access_token)):
    """
    Upload files
    
    - **study_uri**: the uri of the current study. If not given, the default **study** is used.
    """
          
    return await Controller.action(action="upload", data=files, study_uri=study_uri)

@app.post("/download/{uri}", tags=["Upload and download files"])
async def download(uri: str, _: UserData = Depends(check_user_access_token)):
    """
    Download a file
    
    - **uri**: the uri of the file to download
    """
    
    from gws.file import File
    try:
        file = File.get(File.uri == uri)
        return FileResponse(file.path, media_type='application/octet-stream', filename=file.name)
    except:
        raise HTTPException(status_code=404, detail="Item not found")

# ##################################################################
#
# Lab
#
# ##################################################################

@app.get("/lab-instance", tags=["Lab instance"])
async def get_lab_instance_status(_: UserData = Depends(check_user_access_token)):
    """
    Get the current status of the lab    
    """
    
    from gws.lab import Lab
    return Lab.get_status()
  
# ##################################################################
#
# Robot
#
# ##################################################################

@app.post("/run-robot-travel-experiment", tags=["Astro boy travels"])
async def run_robot_travel_experiment(_: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Run robot experiments. The default study is used
    """

    return await Controller._run_robot_travel()

@app.post("/run-robot-super-travel-experiment", tags=["Astro boy travels"])
async def run_robot_super_travel_experiment(_: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Run robot experiments. The default study is used
    """

    return await Controller._run_robot_super_travel()

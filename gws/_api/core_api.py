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
from gws.app import check_is_admin

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
# Queue
#
# ##################################################################

@app.get("/queue", tags=["Queue"], summary="Get the queue")
async def get_queue_details() -> (dict, str,):
    """
    Retrieve details of the queue
    """

    return Controller.get_queue()
    
# ##################################################################
#
# Experiment
#
# ##################################################################

@app.post("/experiment/{uri}/start", tags=["Experiment"], summary="Start an experiment")
async def start_experiment(uri: str, \
                         _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Start an experiment
    
    - **flow**: the flow object 
    """

    return await Controller.start_experiment(uri=uri)

@app.post("/experiment/{uri}/stop", tags=["Experiment"], summary="Stop a running experiment")
async def stop_experiment(uri: str, \
                         _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Stop an experiment
    
    - **uri**: the experiment uri
    """

    return await Controller.stop_experiment(uri=uri)


@app.post("/experiment/{uri}/update", tags=["Experiment"], summary="Update an experiment")
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
    
    return Controller.update_experiment(
        uri = uri, 
        title = title, 
        description = description, 
        data = flow
    )

@app.post("/experiment/{uri}/archive", tags=["Experiment"])
async def archive_experiment(uri:str, \
                             _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Archive an experiment
    
    - **uri**: the uri of the experiment
    """

    return await Controller.action(action="archive", object_type="experiment", object_uri=uri)

@app.post("/experiment/{uri}/unarchive", tags=["Experiment"])
async def unarchive_experiment(uri:str, \
                               _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Unarchive an experiment
    
    - **uri**: the uri of the experiment
    """

    return await Controller.action(action="unarchive", object_type="experiment", object_uri=uri)

@app.post("/experiment/{uri}/validate", tags=["Experiment"], summary="Validate an experiment")
async def validate_experiment(uri: str, \
                              _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Validate a protocol
    
    - **uri**: the uri of the experiment
    """

    return Controller.validate_experiment(uri=uri)

@app.get("/experiment/list", tags=["Experiment"], summary="Get the list of experiments")
async def get_list_of_experiments(page: int = 1, \
                                  number_of_items_per_page: int = 20, \
                                  _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Retrieve a list of experiments. The list is paginated.

    - **page**: the page number 
    - **number_of_items_per_page**: the number of items per page (limited to 50) 
    """

    return Controller.fetch_experiment_list(
        page = page, 
        number_of_items_per_page = number_of_items_per_page
    )

@app.put("/experiment/{uri}", tags=["Experiment"], summary="Create an experiment")
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
    
    return Controller.create_experiment(
        study_uri = study_uri,
        uri = uri,
        title = title, 
        description = description, 
        data = flow
    )

@app.get("/experiment/{uri}", tags=["Experiment"], summary="Get an experiment")
async def get_experiment(uri: str, \
                       _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Retrieve an experiment
    
    - **uri**: the uri of an experiment
    """

    return Controller.fetch_experiment(uri=uri)


# ##################################################################
#
# Protocol
#
# ##################################################################

@app.get("/protocol/list", tags=["Protocol"], summary="Get the list of protocols")
async def get_list_of_protocols(experiment_uri: str = None, \
                                page: int = 1, \
                                number_of_items_per_page: int = 20, \
                                _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Retrieve a list of protocols. The list is paginated.
    
    - **experiment_uri**: the uri of experiment related to the protocol (an experiment is related to one protocol).
    - **page**: the page number 
    - **number_of_items_per_page**: the number of items per page (limited to 50 if no experiment_uri is not given) 
    """

    return Controller.fetch_protocol_list(
        page = page, 
        number_of_items_per_page = number_of_items_per_page,
        experiment_uri = experiment_uri,
    )

@app.get("/protocol/{uri}", tags=["Protocol"], summary="Get a protocol")
async def get_protocol(uri: str, \
                       _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Retrieve a protocol
    
    - **uri**: the uri of the protocol
    """

    return Controller.fetch_protocol(uri = uri)

# ##################################################################
#
# Process
#
# ##################################################################

@app.get("/process/list", tags=["Process"], summary="Get the list of processes")
async def get_list_of_process(experiment_uri: str = None, \
                              page: int = 1, \
                              number_of_items_per_page: int = 20, \
                              _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Retrieve a list of processes. The list is paginated.

    - **page**: the page number 
    - **number_of_items_per_page**: the number of items per page. Defaults to 20 items per page. 
    """

    return Controller.fetch_process_list(
        page = page, 
        number_of_items_per_page = number_of_items_per_page,
        experiment_uri = experiment_uri
    )

@app.get("/process-type/list", tags=["Process"], summary="Get the list of process types")
async def get_list_of_process_types(page: int = 1, \
                                    number_of_items_per_page: int = 20, \
                                    _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Retrieve a list of processes. The list is paginated.

    - **page**: the page number 
    - **number_of_items_per_page**: the number of items per page. Defaults to 20 items per page.
    """

    return Controller.fetch_process_type_list(
        page = page, 
        number_of_items_per_page = number_of_items_per_page
    )

@app.get("/process/{uri}", tags=["Process"], summary="Get a process")
async def get_process(uri: str, \
                       _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Retrieve a process
    
    - **uri**: the uri of the process
    """

    return Controller.fetch_process(uri = uri)

# ##################################################################
#
# Config
#
# ##################################################################

@app.get("/config/list", tags=["Configs"], summary="Get the list of configs")
async def get_list_of_configs(page: int = 1, \
                              number_of_items_per_page: int = 20, \
                              _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Retrieve a list of configs. The list is paginated.

    - **page**: the page number 
    - **number_of_items_per_page**: the number of items per page. Defaults to 20 items per page. 
    """

    return Controller.fetch_config_list(
        page = page, 
        number_of_items_per_page = number_of_items_per_page,
    )

# ##################################################################
#
# Resource
#
# ##################################################################

@app.get("/resource/list", tags=["Resource"], summary="Get the list of resources")
async def get_list_of_resources(experiment_uri: str = None, \
                                page: int = 1, \
                                number_of_items_per_page: int = 20, \
                                _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Retrieve a list of resources. The list is paginated.

    - **experiment_uri**: the uri of the exepriment in which the resource was generated
    - **page**: the page number 
    - **number_of_items_per_page**: the number of items per page. Defaults to 20 items per page.
    """

    return Controller.fetch_resource_list(
        page = page, 
        number_of_items_per_page = number_of_items_per_page, 
        experiment_uri = experiment_uri
    )

# ##################################################################
#
# Get, Post, Put, Delete, Verify
#
# ##################################################################

@app.get("/count/{object_type}", tags=["Models and ViewModels"])
async def count(object_type: str, \
                _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Get the count of objects of a given type
    
    - **object_type**: the object type
    """

    return await Controller.action(
        action = "count", 
        object_type = object_type
    )

@app.post("/view/{object_type}/{object_uri}/archive", tags=["Models and ViewModels"])
async def archive_view_model(object_type: str, \
                             object_uri: str, \
                             _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Archive a ViewModel
    
    - **object_type**: the type of the object to archive.
    - **object_uri**: the uri of the object to archive
    """

    return await Controller.action(
        action = "archive", 
        object_type = object_type, 
        object_uri = object_uri
    )

@app.post("/view/{object_type}/{object_uri}/unarchive", tags=["Models and ViewModels"])
async def unarchive_view_model(object_type: str, \
                               object_uri: str, \
                               _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Archive a ViewModel
    
    - **object_type**: the type of the object to archive.
    - **object_uri**: the uri of the object to archive
    """

    return await Controller.action(
        action = "unarchive", 
        object_type = object_type, 
        object_uri = object_uri
    )

@app.post("/view/{object_type}/{object_uri}/update", tags=["Models and ViewModels"])
async def update_view_model(object_type: str, \
                            object_uri: str, \
                            view_model: ViewModelData, \
                            _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Update a ViewModel
    
    - **object_type**: the type of object of which the ViewModel is attached
    - **view_model**: data of the ViewModel `{uri: "uri_of_the_view_model", data: "parameters_of_the_view_model"}`
    """

    return await Controller.action(
        action = "update", 
        object_type = object_type, 
        object_uri = object_uri, 
        data = view_model.params
    )

@app.get("/view/{object_type}/{object_uris}", tags=["Models and ViewModels"])
async def get_view_model(object_type: str, \
                         object_uris: Optional[str] = "all", \
                         page: int = 1, \
                         number_of_items_per_page: int = 20, \
                         filters: Optional[str] = "{}", \
                         view_params: Optional[str] = "{}", \
                        _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Get a ViewModel
    
    Custom query params depending on the queryied model. 
    
    - **object_type**: the type of the object to fetch. Can be an existing ViewModel or a Viewable object with no ViewModel. In this case, default ViewModel is created and returned.
    - **object_uris**: the uris of the object to fetch. Use comma-separated values to fecth several uris or 'all' to fetch all the entries. When all entries are retrieve, the **filter** parameter can be used.
    - **page**: the page number 
    - **number_of_items_per_page**: the number of items per page. Defaults to 20 items per page.
    - **filters**: filter to use to select data (**object_uris** must be equal to 'all'). The filter is matches using full-text search against to the `title` and the `description`. The format is `filter={"title": "Searched title*", "description": "This is a description for full-text search"}`
    - **view_params**: key,value parameters of the ViewModel. The key,value specifications are given by the method `to_json()` of the corresponding object class. See class documentation.
    """
    
    try:
        params = json.loads(view_params)
    except:
        params = {}
        
    return await Controller.action(
        action = "get", 
        object_type = object_type, 
        object_uri = object_uris, 
        data = params, 
        page = page, 
        number_of_items_per_page = number_of_items_per_page, 
        filters = filters
    )


@app.get("/hash/{object_type}/{object_uri}/verify", tags=["Models and ViewModels"])
async def verify_hash(object_type: str, \
                      object_uri: str, \
                      _: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Verify Model and ViewModel hash.
    
    Verify the integrity of a given object in the db to check if that object has been altered by any unofficial mean
    (e.g. manual changes of data in db, or partial changes without taking care of its dependency chain).
    
    Objects' integrity is based on an algorithm that computes hashes using objects' data and their dependency trees (like in block chain) rendering any data falsification difficult to hide.
    
    - **object_type**: the type of the object to delete.
    - **object_uri**: the uri of the object to delete
    """

    return Controller.verify_hash(
        object_type=object_type, 
        object_uri=object_uri
    )

# ##################################################################
#
# Brick
#
# ##################################################################

#@app.api_route("/brick/{brick_name}/{api_func}", response_class=JSONResponse, methods=["GET", "POST"], tags=["Bricks APIs"])
@app.post("/brick/{brick_name}/{api_func}", response_class=JSONResponse, tags=["Bricks APIs"])
async def call_brick_api(brick_name: Optional[str] = "gws", \
                         api_func: Optional[str] = None, \
                         data: Optional[dict] = {}, \
                         _: UserData = Depends(check_user_access_token)) :
    """
    Call a custom api function of a brick
    
    - **brick_name**: the name of the brick
    - **api_func**: the target api function. 
    - **data**: custom json data
    For example of **brick_name=foo** and **api_func=do-thing**, the method **foo.app.API.do_thing( data )** with be called if it exists. Function **do_thing** must return a JSON response as a dictionnary.
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
            return await async_func(data)
    
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
# User
#
# ##################################################################

@app.get("/user/me", response_model=UserData, tags=["User"])
async def read_user_me(current_user: UserData = Depends(check_user_access_token)):
    """
    Get current user details.
    """
    
    return current_user

@app.get("/user/activity", tags=["User"])
async def get_activity(user_uri:Optional[str] = None, \
                       activity_type:Optional[str] = None, \
                       page: int = 1, \
                       number_of_items_per_page: int = 20, \
                        _: UserData = Depends(check_user_access_token)):
    """
    Get the list of user activities on the lab
    
    - **user_uri**: the uri the user [optional]
    - **activity_type**: the type of the activity to retrieve [optional]. The valid types of activities are: 
      - **CREATE** : the creation of an object
      - **SAVE**   : the saving of an object
      - **START**  : the start of an experiment
      - **STOP**   : the stop of an experiment
      - **DELETE** : the deletion of an experiment
      - **ARCHIVE** : the archive of an object
      - **VALIDATE** : the valdaition of an experiment
      - **HTTP_AUTHENTICATION** : HTTP authentication
      - **HTTP_UNAUTHENTICATION** : HTTP unauthentication
      - **CONSOLE_AUTHENTICATION** : console authentication (through CLI or notebook)
      - **CONSOLE_UNAUTHENTICATION** : console unauthentication
    - **page**: the page number 
    - **number_of_items_per_page**: the number of items per page. Defaults to 20 items per page.
    """
    
    return Controller.fecth_activity_list(
        user_uri = user_uri, 
        activity_type = activity_type,
        page = page, 
        number_of_items_per_page = number_of_items_per_page
    )

# ##################################################################
#
# IO File
#
# ##################################################################


@app.put("/file/upload", tags=["Upload and download files"])
async def upload(files: List[UploadFile] = FastAPIFile(...), \
                 study_uri:Optional[str] = None, \
                 _: UserData = Depends(check_user_access_token)):
    """
    Upload files
    
    - **study_uri**: the uri of the current study. If not given, the default **study** is used.
    """
    
    return await Controller.action(action="upload", data=files, study_uri=study_uri)

@app.get("/file/{uri}/download", tags=["Upload and download files"])
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

@app.get("/lab/instance", tags=["Lab"])
async def get_lab_status(_: UserData = Depends(check_user_access_token)):
    """
    Get lab status
    """
    
    return Controller.get_lab_status()

@app.get("/lab/monitor", tags=["Lab"])
async def get_lab_monitor(page: int = 1, number_of_items_per_page: int = 20,\
                          _: UserData = Depends(check_user_access_token)):
    """
    Get lab monitor    
    """
    
    return Controller.get_lab_monitor()

# ##################################################################
#
# Run adhoc experiment
#
# ##################################################################

@app.post("/run/astro-travel-experiment", tags=["Astro boy travels"])
async def run_astro_travel_experiment(_: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Run astrobot experiments. The default study is used.
    """

    return await Controller._run_robot_travel()

@app.post("/run/astro-super-travel-experiment", tags=["Astro boy travels"])
async def run_astro_super_travel_experiment(_: UserData = Depends(check_user_access_token)) -> (dict, str,):
    """
    Run astrobot experiments. The default study is used.
    """

    return await Controller._run_robot_super_travel()

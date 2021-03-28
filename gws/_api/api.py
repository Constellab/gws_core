# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
from typing import Optional, List

from fastapi import Depends, FastAPI, \
                    UploadFile, Request, \
                    HTTPException, File as FastAPIFile
from fastapi.responses import Response, JSONResponse, RedirectResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

from gws.settings import Settings
from gws.central import Central
from gws.controller import Controller
from gws.model import Model, ViewModel, Experiment

from ._auth_user import OAuth2UserTokenRequestForm, get_current_authenticated_user, get_current_authenticated_admin_user
from ._auth_user import UserData
from gws.http import async_error_track

from starlette_context.middleware import context, ContextMiddleware
middleware = [Middleware(ContextMiddleware)]

app = FastAPI(docs_url="/docs", middleware=middleware)

# Enable core for the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET,HEAD,PUT,PATCH,POST,DELETE"],
    allow_headers=["Origin,X-Requested-With,Content-Type,Accept,Authorization,authorization,X-Forwarded-for,lang"],
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
    
class FlowData(BaseModel):
    uri: Optional[str]
    type: Optional[str] = "gws.model.Job"
    #is_archived: Optional[bool] = False
    #is_deleted: Optional[bool] = False
    #creation_datetime: Optional[str]
    #save_datetime: Optional[str]
    #progress: Optional[float] = 0.0
    process: Optional[ProtocolData]
    config: Optional[ConfigData]
    parent_job_uri: Optional[str]
    experiment_uri: Optional[str]
    layout: Optional[dict] = {}
    jobs: dict
    flows: dict
    
# ##################################################################
#
# List
#
# ##################################################################

@app.get("/experiment/list", tags=["Shortcut operations on experiments"], summary="Get the list of experiments")
async def get_list_of_experiments(page: int = 1, number_of_items_per_page: int = 20, \
                                  current_user: UserData = Depends(get_current_authenticated_user)) -> (dict, str,):
    """
    Retrieve a list of experiments. The list is paginated.

    - **page**: the page number 
    - **number_of_items_per_page**: the number of items per page (limited to 50) 
    """

    return Controller.fetch_experiment_list(
        page=page, 
        number_of_items_per_page=number_of_items_per_page
    )

@app.post("/experiment/save", tags=["Shortcut operations on experiments"], summary="Save an experiment using a existing (or new) job flow")
async def save_experiment(flow: Optional[dict], \
                          current_user: UserData = Depends(get_current_authenticated_user)) -> (dict, str,):
    """
    Save a protocol.
    
    - **flow**: the flow object 
    """
    
    return Controller.save_experiment(data=flow)

@app.post("/experiment/run/", tags=["Shortcut operations on experiments"], summary="Run an experiment")
async def run_experiment(flow: Optional[dict], \
                         current_user: UserData = Depends(get_current_authenticated_user)) -> (dict, str,):
    """
    Run an experiment
    
    - **flow**: the flow object 
    """

    return await Controller.run_experiment(data=flow)

@app.get("/job/flow", tags=["Shortcut operations on experiments"], summary="Get job flow")
async def get_job_flow(protocol_job_uri: str = None, experiment_uri: str = None, \
                       current_user: UserData = Depends(get_current_authenticated_user)) -> (dict, str,):
    """
    Retrieve the job flow of an experiment or a protocol job
    
    - **protocol_job_uri**: the uri of the job (must be a job of a protocol)
    - **experiment_uri**: the uri of an experiment (is not used if job_uri is given)
    """

    return Controller.fetch_job_flow(protocol_job_uri=protocol_job_uri, experiment_uri=experiment_uri)

@app.get("/job/list", tags=["Shortcut operations on experiments"], summary="Get the list of jobs")
async def get_list_of_jobs(experiment_uri: str = None, page: int = 1, number_of_items_per_page: int = 20, \
                           current_user: UserData = Depends(get_current_authenticated_user)) -> (dict, str,):
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

@app.get("/protocol/list", tags=["Shortcut operations on experiments"], summary="Get the list of protocols")
async def get_list_of_protocols(experiment_uri: str = None, job_uri: str = None, \
                                page: int = 1, number_of_items_per_page: int = 20, \
                                current_user: UserData = Depends(get_current_authenticated_user)) -> (dict, str,):
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

@app.post("/protocol/save", tags=["Shortcut operations on experiments"], summary="Save a protocol using a existing (or new) job flow")
async def save_protocol(flow: Optional[dict], \
                        current_user: UserData = Depends(get_current_authenticated_user)) -> (dict, str,):
    """
    Save a protocol
    
    - **flow**: the flow object 
    """

    return await Controller.save_protocol(data=flow)


@app.get("/process/list", tags=["Shortcut operations on experiments"], summary="Get the list of processes")
async def get_list_of_process(job_uri: str = None, \
                              page: int = 1, number_of_items_per_page: int = 20, \
                              current_user: UserData = Depends(get_current_authenticated_user)) -> (dict, str,):
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

@app.get("/config/list", tags=["Shortcut operations on experiments"], summary="Get the list of configs")
async def get_list_of_configs(job_uri: str = None, \
                              page: int = 1, number_of_items_per_page: int = 20, \
                              current_user: UserData = Depends(get_current_authenticated_user)) -> (dict, str,):
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

@app.get("/resource/list", tags=["Shortcut operations on experiments"], summary="Get the list of resources")
async def get_list_of_resources(job_uri: str = None, \
                                experiment_uri: str = None, page: int = 1, number_of_items_per_page: int = 20, \
                                current_user: UserData = Depends(get_current_authenticated_user)) -> (dict, str,):
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

@app.get("/count/{object_type}/", tags=["CRUD operations on view models"])
async def count(object_type: str, \
                current_user: UserData = Depends(get_current_authenticated_user)) -> (dict, str,):
    """
    Get the count of objects of a given type
    
    - **object_type**: the object type
    """

    return await Controller.action(action="count", object_type=object_type)

@app.get("/view/{object_type}/{object_uris}/", tags=["CRUD operations on view models"])
async def get_view_model(object_type: str, object_uris: Optional[str] = "all", \
                        page: int = 1, number_of_items_per_page: int = 20, \
                        filters: Optional[str] = "{}", view_params: Optional[str] = "{}", \
                        current_user: UserData = Depends(get_current_authenticated_user)) -> (dict, str,):
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

@app.put("/view/{object_type}/", tags=["CRUD operations on view models"])
async def update_view_model(object_type: str, view_model: ViewModelData, \
                            current_user: UserData = Depends(get_current_authenticated_user)) -> (dict, str,):
    """
    Update a ViewModel
    
    - **object_type**: the type of object of which the ViewModel is attached
    - **view_model**: data of the ViewModel `{uri: "uri_of_the_view_model", data: "parameters_of_the_view_model"}`
    """

    return await Controller.action(action="update", object_type=object_type, object_uri=view_model.uri, data=view_model.params)

@app.delete("/view/{object_type}/{object_uri}/", tags=["CRUD operations on view models"])
async def delete_view_model(object_type: str, object_uri: str, \
                            current_user: UserData = Depends(get_current_authenticated_user)) -> (dict, str,):
    """
    Delete a ViewModel
    
    - **object_type**: the type of the object to delete.
    - **object_uri**: the uri of the object to delete
    """

    return await Controller.action(action="delete", object_type=object_type, object_uri=object_uri)

# ##################################################################
#
# IO File
#
# ##################################################################

@app.api_route("/brick/{brick_name}/{api_func}", response_class=JSONResponse, methods=["GET", "POST"], tags=["Custom brick api"])
async def call_brick_api(request: Request, \
                         brick_name: Optional[str] = "gws", api_func: Optional[str] = None, \
                         current_user: UserData = Depends(get_current_authenticated_user)) :
    """
    Call a custom api function of a brick
    
    - **brick_name**: the name of the brick
    - **api_func**: the target api function. 
    
    For example of **brick_name=foo** and **api_func=bar**, the method **foo.app.API.bar( request: fastapi.requests.Request )** with be called if it exists. The current **request** will be passed to the function.
    """
    
    brick_app_module = importlib.import_module(f"{brick_name}.app")
    api_t = getattr(brick_app_module, "API", None)

    try:
        async_func = getattr(api_t, api_func.replace("-","_").lower(), None)
        results = await async_func(request)
        return results
    except Exception as err:
        return {"exception": {"id": "UNEXPECTED_ERROR", "message": f"An unexpected error occured. Message: {err}"}}

        
# ##################################################################
#
# IO File
#
# ##################################################################


@app.post("/upload", tags=["Upload and download files"])
async def upload(files: List[UploadFile] = FastAPIFile(...), study_uri:Optional[str] = None, \
                 current_user: UserData = Depends(get_current_authenticated_user)):
    """
    Upload files
    
    - **study_uri**: the uri of the current study. If not given, the default **study** is used.
    """
          
    return await Controller.action(action="upload", data=files, study_uri=study_uri)

@app.post("/download/{uri}", tags=["Upload and download files"])
async def download(uri: str, current_user: UserData = Depends(get_current_authenticated_user)):
    """
    Download file
    """
    
    from gws.file import File
    try:
        file = File.get(File.uri == uri)
        return FileResponse(file.path, media_type='application/octet-stream', filename=file.name)
    except:
        raise HTTPException(status_code=404, detail="Item not found")

# ##################################################################
#
# User
#
# ##################################################################

@app.get("/user/login/{uri}/{token}", tags=["User management"])
async def login_user(request: Request, uri: str, token: str, \
                     redirect_url: str = "/", object_type: str=None, object_uri: str=None):
    
    form_data: OAuth2UserTokenRequestForm = Depends()
    form_data.uri = uri
    form_data.token = token
    
    print("yyyyyyyy")
    
    from ._auth_user import login
    return await login(form_data=form_data)

@app.get("/user/logout", response_model=UserData, tags=["User management"])
async def logout_user(request: Request, current_user: UserData = Depends(get_current_authenticated_user)):
    from ._auth_user import logout
    return await logout(current_user)

@app.get("/user/me/", response_model=UserData, tags=["User management"])
async def read_users_me(current_user: UserData = Depends(get_current_authenticated_user)):
    return current_user

@app.post("/user/create", tags=["User management"])
async def create_user(user: UserData, current_user: UserData = Depends(get_current_authenticated_admin_user)):
    return Central.create_user(user.dict())

@app.get("/user/{user_uri}", tags=["User management"])
async def get_user(user_uri : str):
    return Central.get_user_status(user_uri)

@app.get("/user/{user_uri}/activate", tags=["User management"])
async def activate_user(user_uri : str, current_user: UserData = Depends(get_current_authenticated_admin_user)):
    return Central.activate_user(user_uri)

@app.get("/user/{user_uri}/deactivate", tags=["User management"])
async def deactivate_user(user_uri : str, current_user: UserData = Depends(get_current_authenticated_admin_user)):
    return  Central.deactivate_user(user_uri)

# ##################################################################
#
# Lab
#
# ##################################################################

@app.get("/lab-instance", tags=["Lab api"])
async def get_lab_instance_status(current_user: UserData = Depends(get_current_authenticated_user)):
    from gws.lab import Lab
    return Lab.get_status()

# ##################################################################
#
# Robot
#
# ##################################################################

@app.post("/run-robot-travel-experiment", tags=["Astro boy travels"])
async def run_robot_travel_experiment(current_user: UserData = Depends(get_current_authenticated_user)) -> (dict, str,):
    """
    Run robot experiments. The default study is used
    """

    return await Controller._run_robot_travel()

@app.post("/run-robot-super-travel-experiment", tags=["Astro boy travels"])
async def run_robot_super_travel_experiment(current_user: UserData = Depends(get_current_authenticated_user)) -> (dict, str,):
    """
    Run robot experiments. The default study is used
    """

    return await Controller._run_robot_super_travel()
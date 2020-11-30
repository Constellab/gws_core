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

prism_app = FastAPI(docs_url="/apidocs")

class _ViewModel(BaseModel):
    uri: str
    data: dict

# ##################################################################
#
# List
#
# ##################################################################

@prism_app.get("/experiment/list")
async def get_list_of_experiments(page: int = 1) -> (dict, str,):
    """
    Retrieve a list of Model or ViewMpdel
    """

    return Controller.fetch_experiment_list(page=page, return_format="json")

@prism_app.get("/job/list")
async def get_list_of_jobs(experiment_uri: str = None, page: int = 1) -> (dict, str,):
    """
    Retrieve a list of Model or ViewMpdel
    """

    return Controller.fetch_job_list(page=page, experiment_uri=experiment_uri, return_format="json")

@prism_app.get("/protocol/list")
async def get_list_of_protocols(job_uri: str = None, page: int = 1) -> (dict, str,):
    """
    Retrieve a list of Model or ViewMpdel
    """

    return Controller.fetch_protocol_list(page=page, job_uri=job_uri, return_format="json")

@prism_app.get("/process/list")
async def get_list_of_process(job_uri: str = None, page: int = 1) -> (dict, str,):
    """
    Retrieve a list of Model or ViewMpdel
    """

    return Controller.fetch_process_list(page=page, job_uri=job_uri, return_format="json")

@prism_app.get("/config/list")
async def get_list_of_configs(job_uri: str = None, page: int = 1) -> (dict, str,):
    """
    Retrieve a list of Model or ViewMpdel
    """

    return Controller.fetch_config_list(page=page, job_uri=job_uri, return_format="json")

@prism_app.get("/resource/list")
async def get_list_of_resources(job_uri: str = None, experiment_uri: str = None, page: int = 1) -> (dict, str,):
    """
    Retrieve a list of Model or ViewModel
    """

    return Controller.fetch_resource_list(page=page, experiment_uri=experiment_uri, job_uri=job_uri, return_format="json")

class _RunData(BaseModel):
    process_uri: str
    process_type: str
    params: dict

@prism_app.post("/run")
async def run_process( run_data: _RunData ) -> (dict, str,):
    """
    Run robot experiments
    """

    return await Controller.action(action="run")

@prism_app.post("/run-robot")
async def run_robot_experiment() -> (dict, str,):
    """
    Run robot experiments
    """

    return await Controller._run_robot()

# ##################################################################
#
# Get, Post, Put, Delete
#
# ##################################################################

@prism_app.get("/{model_type}/{uri}")
async def get_model_or_viewmodel(model_type: str, uri: str) -> (dict, str,):
    """
    Get and render a ViewModel
    """

    return Controller.action(action="get", model_type=model_type, uri=uri, return_format="json")

@prism_app.post("/")
async def post_view_model(model_type: str, vmodel: _ViewModel) -> (dict, str,):
    """
    Post an render a ViewModel
    """

    return Controller.action(action="post", model_type=model_type, uri=vmodel.uri, data=vmodel.data, return_format="json")


@prism_app.put("/{model_type}/")
async def put_view_model(model_type: str, vmodel: _ViewModel) -> (dict, str,):
    """
    Post and render a ViewModel
    """

    return Controller.action(action="put", model_type=model_type, uri=vmodel.uri, data=vmodel.data, return_format="json")

@prism_app.delete("/{model_type}/{uri}/")
async def delete_view_model(model_type: str, uri: str) -> (dict, str,):
    """
    Post a ViewModel and render its
    """

    return Controller.action(action="delete", model_type=model_type, uri=uri)

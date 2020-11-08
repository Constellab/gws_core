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

prism_app = FastAPI()

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

    try:
        response = Controller.fetch_experiment_list(page=page, return_format="json")
        return { "status": True, "response": response }
    except Exception as err:
        return {"status": False, "response": f"{err}"}

@prism_app.get("/job/list")
async def get_list_of_jobs(experiment_uri: str = None, page: int = 1) -> (dict, str,):
    """
    Retrieve a list of Model or ViewMpdel
    """

    try:
        response = Controller.fetch_job_list(page=page, experiment_uri=experiment_uri, return_format="json")
        return { "status": True, "response": response }
    except Exception as err:
        return {"status": False, "response": f"{err}"}

@prism_app.get("/protocol/list")
async def get_list_of_protocols(job_uri: str = None, page: int = 1) -> (dict, str,):
    """
    Retrieve a list of Model or ViewMpdel
    """

    try:
        response = Controller.fetch_protocol_list(page=page, job_uri=job_uri, return_format="json")
        return { "status": True, "response": response }
    except Exception as err:
        return {"status": False, "response": f"{err}"}

@prism_app.get("/process/list")
async def get_list_of_process(job_uri: str = None, page: int = 1) -> (dict, str,):
    """
    Retrieve a list of Model or ViewMpdel
    """

    try:
        response = Controller.fetch_process_list(page=page, job_uri=job_uri, return_format="json")
        return { "status": True, "response": response }
    except Exception as err:
        return {"status": False, "response": f"{err}"}

@prism_app.get("/config/list")
async def get_list_of_configs(job_uri: str = None, page: int = 1) -> (dict, str,):
    """
    Retrieve a list of Model or ViewMpdel
    """

    try:
        response = Controller.fetch_config_list(page=page, job_uri=job_uri, return_format="json")
        return { "status": True, "response": response }
    except Exception as err:
        return {"status": False, "response": f"{err}"}

@prism_app.get("/resource/list")
async def get_list_of_resources(job_uri: str = None, experiment_uri: str = None, page: int = 1) -> (dict, str,):
    """
    Retrieve a list of Model or ViewModel
    """

    try:
        response = Controller.fetch_resource_list(page=page, experiment_uri=experiment_uri, job_uri=job_uri, return_format="json")
        return { "status": True, "response": response }
    except Exception as err:
        return {"status": False, "response": f"{err}"}

class _RunData(BaseModel):
    process_uri: str
    process_type: str
    params: dict

@prism_app.post("/run")
async def run_process( run_data: _RunData ) -> (dict, str,):
    """
    Run robot experiments
    """

    try:
        tf = await Controller.action(action="run", )
        return { "status": tf, "response": "" }
    except Exception as err:
        return {"status": False, "response": f"{err}"}

@prism_app.post("/run-robot")
async def run_robot_experiment() -> (dict, str,):
    """
    Run robot experiments
    """

    try:
        tf = await Controller._run_robot()
        return { "status": tf, "response": "" }
    except Exception as err:
        return {"status": False, "response": f"{err}"}

# ##################################################################
#
# Get, Post, Put, Delete
#
# ##################################################################

@prism_app.get("/g/{rtype}/{uri}")
async def get_model_or_view_model(rtype: str, uri: str) -> (dict, str,):
    """
    Get and render a ViewModel
    """

    try:
        response = Controller.action(action="get", rtype=rtype, uri=uri, return_format="json")
        return { "status": True, "response": response }
    except Exception as err:
        return {"status": False, "response": f"{err}"}

@prism_app.post("/g/")
async def post_view_model(rtype: str, vmodel: _ViewModel) -> (dict, str,):
    """
    Post an render a ViewModel
    """

    try:
        response = Controller.action(action="post", rtype=rtype, uri=vmodel.uri, data=vmodel.data, return_format="json")
        return { "status": True, "response": response }
    except Exception as err:
        return {"status": False, "response": f"{err}"}

@prism_app.put("/g/{rtype}/")
async def put_view_model(rtype: str, vmodel: _ViewModel) -> (dict, str,):
    """
    Post and render a ViewModel
    """

    try:
        response = Controller.action(action="put", rtype=rtype, uri=vmodel.uri, data=vmodel.data, return_format="json")
        return { "status": True, "response": response }
    except Exception as err:
        return {"status": False, "response": f"{err}"}

@prism_app.delete("/g/{rtype}/{uri}/")
async def delete_view_model(rtype: str, uri: str) -> (dict, str,):
    """
    Post a ViewModel and render its
    """

    try:
        response = Controller.action(action="delete", rtype=rtype, uri=uri, return_format="json")
        return { "status": True, "response": response }
    except Exception as err:
        return {"status": False, "response": f"{err}"}


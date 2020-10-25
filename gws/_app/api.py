# Core GWS app module
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from starlette.authentication import requires
from starlette.responses import JSONResponse

@requires("authenticated")
async def lab_status_page(request):
    from gws.lab import Lab
    return JSONResponse(Lab.get_status())

@requires("authenticated")
async def create_experiment_page(request):
    from gws.central import Central
    try:
        uri = request.path_params["uri"]
        data = await request.json()
        tf = Central.create_experiment(uri, data)
        return JSONResponse({
            "status": tf,
            "message" : ""
        })
    except Exception as err:
        return JSONResponse({
            "status": False,
            "message": str(err)
        })

@requires("authenticated")
async def get_experiment_page(request):
    from gws.model import Experiment
    uri = request.path_params["uri"]
    e = Experiment.get_by_uri(uri)
    return JSONResponse({
        "uri": e.uri,
        "user_uri": e.user.uri,
        "project_uri": e.project.uri
    })
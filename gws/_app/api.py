# Core GWS app module
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from starlette.authentication import requires
from starlette.responses import JSONResponse
from gws.central import Central

@requires("authenticated")
async def lab_status_page(request):
    from gws.lab import Lab
    return JSONResponse(Lab.get_status())

@requires("authenticated")
async def activate_user_page(request):
    uri = request.path_params["uri"]
    try:
        tf = Central.activate_user(uri)
        return JSONResponse({
            "status": tf,
            "message" : ""
        })
    except Exception as err:
        return JSONResponse({
            "status": False,
            "message" : str(err)
        })

@requires("authenticated")
async def deactivate_user_page(request):
    uri = request.path_params["uri"]
    try:
        tf = Central.deactivate_user(uri)
        return JSONResponse({
            "status": tf,
            "message" : ""
        })
    except Exception as err:
        return JSONResponse({
            "status": False,
            "message" : str(err)
        })

@requires("authenticated")
async def create_user_page(request):
    try:
        data = await request.json()
        tf = Central.create_user(data)
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
async def open_experiment_page(request):
    try:
        data = await request.json()
        tf = Central.open_experiment(data)
        request.session['user_uri'] = data['user_uri']
        request.session['experiment_uri'] = data['uri']
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
async def close_experiment_page(request):
    request.session['experiment_uri'] = ''
    return JSONResponse({
        "status": True,
        "message" : ""
    })
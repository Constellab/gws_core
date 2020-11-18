# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Optional

from fastapi import Depends, FastAPI, Request
from fastapi.responses import Response, RedirectResponse
from pydantic import BaseModel

from gws.settings import Settings
from gws.central import Central

from gws._auth.central import   (   check_api_key, 
                                    generate_user_access_token as _generate_user_access_token
                                )

from gws._auth.user import (    OAuth2UserTokenRequestForm, _Token, 
                                login, logout,
                                get_current_active_user
                            )
central_app = FastAPI(docs_url="/apidocs")

# User
class _User(BaseModel):
    uri: str

@central_app.get("/login/{user_access_token}")
async def login_user(request: Request, user_access_token: str, redicrect_url: str = "/"):
    form_data: OAuth2UserTokenRequestForm = Depends()
    form_data.user_access_token = user_access_token
    return await login(form_data=form_data, redicrect_url=redicrect_url)

@central_app.get("/logout", response_model=_User)
async def logout_user(request: Request, current_user: _User = Depends(get_current_active_user)):
    return await logout(current_user, redicrect_url="/page/gws/logout")

@central_app.get("/open-jupyter-lab", response_model=_User)
async def open_jupyter_lab(current_user: _User = Depends(get_current_active_user)):
    return current_user

@central_app.get("/me/", response_model=_User)
async def read_users_me(current_user: _User = Depends(get_current_active_user)):
    return current_user

@central_app.post("/user/add")
async def add_user_to_the_lab(user: _User):
    try:
        user_dict = Central.create_user(user.dict())
        return { "status": True, "data" : user_dict }
    except Exception as err:
        return { "status": False, "data": str(err) }

class _UserUri(BaseModel):
    uri: str


@central_app.post("/user/generate-access-token", response_model=_Token)
async def generate_user_access_token(user_uri: _UserUri, _ = Depends(check_api_key)):
    return await _generate_user_access_token(user_uri.uri)

@central_app.get("/user/{user_uri}")
async def get_user(user_uri : str):
    try:
        user_dict = Central.get_user_status(user_uri)
        return { "status": True, "data" : user_dict }
    except Exception as err:
        return { "status": False, "data" : str(err) }

@central_app.get("/user/{user_uri}/activate")
async def activate_user(user_uri : str):
    try:
        tf = Central.activate_user(user_uri)
        return { "status": tf, "data" : "" }
    except Exception as err:
        return { "status": False, "data" : str(err) }

@central_app.get("/user/{user_uri}/deactivate")
async def deactivate_user(user_uri : str):
    try:
        tf = Central.deactivate_user(user_uri)
        return { "status": tf, "data" : "" }
    except Exception as err:
        return { "status": False, "data" : str(err) }

@central_app.get("/lab-instance")
async def get_lab_instance_status():
    from gws.lab import Lab
    return { "status": True, "data" : Lab.get_status() }

class _ApiKey(BaseModel):
    key: str

@central_app.put("/api-key")
async def set_central_api_key(api_key: _ApiKey):
    settings = Settings.retrieve()
    settings.set_data("central_api_key", api_key.key)
    tf = settings.save()
    return { "status": tf, "data" : "" }

# #########################################################################@
#
# Experiment & Protocol Routes
#
# #########################################################################@

class _Protocol(BaseModel):
    uri: str
    graph: Optional[dict] = None

class _Experiment(BaseModel):
    uri: str
    protocol: _Protocol
    
@central_app.post("/experiment/create")
async def create_experiment(exp: _Experiment):
    try:
        exp = Central.create_experiment(exp.dict())
        return { 
            "status": True, 
            "data" : {
                "experiment": {
                    "uri": exp.uri
                },
                "protocol": {
                    "uri": exp.protocol.uri
                }
            }
        }
    except Exception as err:
        return { "status": False, "data": str(err) }

@central_app.put("/experiment/{experiment_uri}/close")
async def close_experiment(request):
    return { "status": True, "data" : ""}

@central_app.delete("/experiment/{experiment_uri}")
async def delete_experiment(request):
    return { "status": True, "data" : ""}

@central_app.get("/protocol/{protocol_uri}")
async def get_protocol(protocol_uri: str):
    try:
        proto_dict = Central.get_protocol(protocol_uri)
        return { "status": True, "data" : proto_dict }
    except Exception as err:
        return { "status": False, "data" : str(err) }
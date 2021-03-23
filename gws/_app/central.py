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

# ##################################################################
#
# User
#
# ##################################################################

class _User(BaseModel):
    uri: str
    token: str
    email: str
    group: str = "user"
    is_active: bool = True
    is_locked: bool = False

class _UserUri(BaseModel):
    uri: str
        
@central_app.get("/login/{user_access_token}", tags=["User api"])
async def login_user(request: Request, user_access_token: str, redirect_url: str = "/", object_type: str=None, object_uri: str=None):
    form_data: OAuth2UserTokenRequestForm = Depends()
    form_data.user_access_token = user_access_token

    return await login(form_data=form_data)

@central_app.get("/logout", response_model=_User, tags=["User api"])
async def logout_user(request: Request, current_user: _User = Depends(get_current_active_user)):
    return await logout(current_user)

@central_app.get("/me/", response_model=_User, tags=["User api"])
async def read_users_me(current_user: _User = Depends(get_current_active_user)):
    return current_user

@central_app.post("/user/create", tags=["User api"])
async def create_user(user: _User):
    return Central.create_user(user.dict())

@central_app.post("/user/generate-access-token", response_model=_Token, tags=["User api"])
async def generate_user_access_token(user_uri: _UserUri, _ = Depends(check_api_key)):
    return await _generate_user_access_token(user_uri.uri)

@central_app.get("/user/{user_uri}", tags=["User api"])
async def get_user(user_uri : str):
    return Central.get_user_status(user_uri)

@central_app.get("/user/{user_uri}/activate", tags=["User api"])
async def activate_user(user_uri : str):
    return Central.activate_user(user_uri)

@central_app.get("/user/{user_uri}/deactivate", tags=["User api"])
async def deactivate_user(user_uri : str):
    return  Central.deactivate_user(user_uri)

@central_app.get("/user/{user_uri}/lock", tags=["User api"])
async def lock_user(user_uri : str):
    return  Central.lock_user(user_uri)

@central_app.get("/user/{user_uri}/unlock", tags=["User api"])
async def unlock_user(user_uri : str):
    return  Central.unlock_user(user_uri)

# ##################################################################
#
# Lab
#
# ##################################################################

@central_app.get("/lab-instance", tags=["Lab api"])
async def get_lab_instance_status():
    from gws.lab import Lab
    return Lab.get_status()

# ##################################################################
#
# Central
#
# ##################################################################

class _CentralApiKey(BaseModel):
    key: str
        
@central_app.put("/central-api-key", tags=["Lab api"])
async def set_central_api_key(api_key: _CentralApiKey):
    settings = Settings.retrieve()
    settings.set_data("central_api_key", api_key.key)
    tf = settings.save()
    return { "status": tf }

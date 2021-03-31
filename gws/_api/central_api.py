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
from starlette_context import context
from starlette_context.middleware import ContextMiddleware

from pydantic import BaseModel

from gws.settings import Settings
from gws.central import Central
from gws.controller import Controller
from gws.model import Model, ViewModel, Experiment
from gws.http import async_error_track

from ._auth_user import UserData, \
                        OAuth2UserTokenRequestForm, \
                        get_current_authenticated_user, \
                        get_current_authenticated_admin_user, \
                        login as _login, \
                        logout as _logout

from ._auth_central import  check_central_api_key, \
                            generate_user_access_token as _generate_user_access_token
app = FastAPI(docs_url="/docs")

# Enable core for the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET,HEAD,PUT,PATCH,POST,DELETE"],
    allow_headers=["Origin,X-Requested-With,Content-Type,Accept,Authorization,authorization,X-Forwarded-for,lang"],
)

app.add_middleware(
    ContextMiddleware
)

class TokenData(BaseModel):
    access_token: str
    token_type: str
        
class UserUriData(BaseModel):
     uri: str
            
# ##################################################################
#
# User
#
# ##################################################################

@app.post("/user/generate-access-token", response_model=TokenData, tags=["User management"])
async def generate_user_access_token(user_uri: UserUriData, _ = Depends(check_central_api_key)):
    """
    Generate a temporary access token for a user.
    
    - **user_uri**: the user uri
    
    For example:
    `
    curl -X "POST" \
      "${LAB_URL}/central-api/user/generate-access-token" \
      -H "Accept: application/json" \
      -H "Authorization: api-key ${CENTRAL_API_KEY}" \
      -H "Content-Type: application/json" \
      -d "{\"uri\": \"${USER_URI}\"}"
    `
    """
    
    return await _generate_user_access_token(user_uri.uri)

@app.get("/user/login/{access_token}", tags=["User api"])
async def login_user(request: Request, \
                     access_token: str, redirect_url: str = "/", \
                     object_type: str=None, object_uri: str=None):
    
    form_data: OAuth2UserTokenRequestForm = Depends()
    form_data.access_token = access_token
    return await _login(form_data=form_data)

@app.get("/user/logout", response_model=UserData, tags=["User management"])
async def logout_user(request: Request, current_user: UserData = Depends(get_current_authenticated_user)):
    return await _logout(current_user)

@app.get("/user/me/", response_model=UserData, tags=["User management"])
async def read_users_me(current_user: UserData = Depends(get_current_authenticated_user)):
    return current_user

@app.post("/user/create", tags=["User management"])
async def create_user(user: UserData, current_user: UserData = Depends(get_current_authenticated_admin_user)):
    return Central.create_user(user.dict())

@app.get("/user/test", tags=["User management"])
async def get_user_test():
    from gws.model import User
    o = User.get_owner()
    s = User.get_sysuser()
    return {
        "owner": {
            "uri": o.uri,
            "token": o.token
        },
        "sys": {
            "uri": s.uri,
            "token": s.token
        }
    }

    #return Central.get_user_status(user_uri)

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
# Central
#
# ##################################################################
 
class CentralApiKeyData(BaseModel):
    key: str
         
@app.put("/central/apikey", tags=["API key"])
async def set_central_api_key(api_key: CentralApiKeyData):
    return  Central.set_api_key(api_key.key)

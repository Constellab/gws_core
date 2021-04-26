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
from gws.http import *

from ._auth_user import UserData, check_user_access_token

from ._auth_central import  check_central_api_key, \
                            generate_user_access_token as _generate_user_access_token

app = FastAPI(docs_url="/docs")

# Enable core for the API
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex="^(.*)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
async def generate_user_access_token(user_uri: UserUriData, \
                                     _ = Depends(check_central_api_key)):
    """
    Generate a temporary access token for a user.
    
    - **user_uri**: the user uri
    
    For example:
    
    `
    curl -X "POST" \
      "${LAB_URL}/central-api/user/generate-access-token" \
      -H "Accept: application/json" \
      -H "Authorization: api-key ${API_KEY}" \
      -H "Content-Type: application/json" \
      -d "{\"uri\": \"${URI}\"}"
    `
    """
    
    return await _generate_user_access_token(user_uri.uri)

@app.post("/user/create", tags=["User management"])
async def create_user(user: UserData, _: UserData = Depends(check_central_api_key)):
    try:
        return Central.create_user(user.dict())
    except Exception as err:
        raise HTTPInternalServerError(detail=f"Cannot create the user. Error: {err}")
        
@app.get("/user/test", tags=["User management"])
async def get_user_test():
    """
    Testing API user details 
    """
    
    from gws.model import User
    return {
        "owner": {
            "uri": User.get_owner().uri,
        },
        "sys": {
            "uri": User.get_sysuser().uri,
        }
    }

@app.get("/user/{user_uri}", tags=["User management"])
async def get_user(user_uri : str, _: UserData = Depends(check_central_api_key)):
    """
    Get the details of a user. Require central privilege.
    
    - **user_uri**: the user uri
    """
    try:
        return Central.get_user_status(user_uri)
    except Exception as err:
        raise HTTPInternalServerError(detail=f"Cannot get the user. Error: {err}")

@app.get("/user/{user_uri}/activate", tags=["User management"])
async def activate_user(user_uri : str, _: UserData = Depends(check_central_api_key)):
    """
    Activate a user. Require central privilege.
    
    - **user_uri**: the user uri
    """
    
    try:
        return Central.activate_user(user_uri)
    except Exception as err:
        raise HTTPInternalServerError(detail=f"Cannot activate the user. Error: {err}")
        
@app.get("/user/{user_uri}/deactivate", tags=["User management"])
async def deactivate_user(user_uri : str, _: UserData = Depends(check_central_api_key)):
    """
    Deactivate a user. Require central privilege.
    
    - **user_uri**: the user uri
    """
    
    try:
        return  Central.deactivate_user(user_uri)
    except Exception as err:
        raise HTTPInternalServerError(detail=f"Cannot deactivate the user. Error: {err}")

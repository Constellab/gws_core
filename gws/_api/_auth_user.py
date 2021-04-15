# Core GWS app module
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import jwt

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.responses import Response
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.param_functions import Form

from passlib.context import CryptContext
from pydantic import BaseModel

from gws.model import User
from gws.controller import Controller
from gws.settings import Settings
from ._oauth2_user_cookie_scheme import oauth2_user_cookie_scheme


settings = Settings.retrieve()
SECRET_KEY = settings.data.get("secret_key")
ALGORITHM = "HS256"

class OAuth2UserTokenRequestForm:
    def __init__(
        self,
        grant_type: str = Form(None, regex="password"),
        token: str = Form(...),
        scope: str = Form(""),
        client_id: Optional[str] = Form(None),
        client_secret: Optional[str] = Form(None),
    ):
        self.grant_type = grant_type
        self.token = token
        self.scopes = scope.split()
        self.client_id = client_id
        self.client_secret = client_secret

class UserData(BaseModel):
    uri: str
    email: str = ""
    first_name: str = ""
    last_name: str = ""
    group: dict = "user"
    is_active: bool
    is_admin: bool

# -- A --

# -- C --


async def check_user_access_token(token: str = Depends(oauth2_user_cookie_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
 
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        uri: str = payload.get("sub")
        if uri is None:
            raise credentials_exception
    except Exception:
        # -> An excpetion occured
        # -> Try to unauthenticate the current user
        try:
            user = Controller.get_current_user()
            if user:
                User.unauthenticate(uri=user.uri)
                
        except:
            pass
        
        raise credentials_exception

    try:
        db_user = User.get(User.uri == uri)
        if not User.authenticate(uri=db_user.uri):
            raise credentials_exception
            
        return UserData(
            uri=db_user.uri, 
            is_active=db_user.is_active, 
            is_admin=db_user.is_admin,
        )
    except:
        raise credentials_exception


async def check_admin_access_token(current_user: UserData = Depends(check_user_access_token)):
    if not current_user.is_admin:
        raise HTTPException(status_code=400, detail="Require higher privilege")
    
    return current_user
 

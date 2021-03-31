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
COOKIE_ACCESS_TOKEN_EXPIRE_MINUTES = 60    #1 hour
COOKIE_MAX_AGE_SECONDS = 3*60*60*24        #3 days 

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
    token: str
    is_active: bool
    is_admin: bool
    is_authenticated: bool

# -- A --

def authenticate_user(access_token: str):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        uri: str = payload.get("sub")
        token: str = payload.get("token")
        if uri is None or token is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
    
    # check uri and token in db
    db_user = User.authenticate(uri=uri, token=token)

    if db_user:
        return UserData(
            uri=db_user.uri, 
            token=db_user.uri,
            is_active=db_user.is_active,
            is_admin=db_user.is_admin,
            is_authenticated=db_user.is_authenticated
        )
    else:
        raise credentials_exception
    
# -- C --

def create_cookie_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# -- G --

async def get_current_user(token: str = Depends(oauth2_user_cookie_scheme)):
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
        raise credentials_exception

    try:
        db_user = User.get(User.uri == uri)
        if not db_user.is_active:
            raise credentials_exception
            
        return UserData(
            uri=db_user.uri, 
            token=db_user.token, 
            is_active=db_user.is_active, 
            is_admin=db_user.is_admin,
            is_authenticated=db_user.is_authenticated
        )
    except:
        raise credentials_exception

async def check_authenticate_user(current_user: UserData = Depends(get_current_user)):
    if not current_user.is_authenticated:
        raise HTTPException(status_code=400, detail="Not authenticated user")
    return True

async def get_current_authenticated_user(current_user: UserData = Depends(get_current_user)):
    if not current_user.is_authenticated:
        raise HTTPException(status_code=400, detail="Not authenticated user")
    
    Controller.set_current_user(current_user)  #<- globally set current_user to the Controller 
    return current_user

async def get_current_authenticated_admin_user(token: str = Depends(oauth2_user_cookie_scheme)):
    current_user = get_current_authenticated_user(token)
    if not current_user.is_admin:
        raise HTTPException(status_code=400, detail="Non admin user")
    
    return current_user
 
# -- L --

async def login(form_data: OAuth2UserTokenRequestForm = Depends(), redirect_url: str = "/"):

    user = authenticate_user(access_token=form_data.access_token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid uri or token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=COOKIE_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_cookie_access_token(
        data={
            "sub": user.uri,
        }, 
        expires_delta=access_token_expires
    )
    
    token = jsonable_encoder(access_token)
    
    response = JSONResponse(content={"status": True})
    response.set_cookie(
        "Authorization",
        value=f"Bearer {token}",
        httponly=True,
        max_age=COOKIE_MAX_AGE_SECONDS,
        expires=COOKIE_MAX_AGE_SECONDS,
    )
    return response

async def logout(current_user: UserData, redirect_url: str = "/"):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        User.unauthenticate(uri = current_user.uri)
        response = JSONResponse(content={"status": True})
        response.delete_cookie("Authorization")
        return response
    except:
        raise credentials_exception

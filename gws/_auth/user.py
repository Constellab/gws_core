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

from gws.user import User
from gws.settings import Settings
from gws._auth.user_token_cookie import oauth2_cookie_scheme

settings = Settings.retrieve()
SECRET_KEY = settings.data.get("secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60*24     #1 day
COOKIE_MAX_AGE_SECONDS = 60*60*24       #1 day 

class OAuth2UserTokenRequestForm:
    def __init__(
        self,
        grant_type: str = Form(None, regex="password"),
        user_access_token: str = Form(...),
        scope: str = Form(""),
        client_id: Optional[str] = Form(None),
        client_secret: Optional[str] = Form(None),
    ):
        self.grant_type = grant_type
        self.user_access_token = user_access_token
        self.scopes = scope.split()
        self.client_id = client_id
        self.client_secret = client_secret

class _User(BaseModel):
    c_key: str
    uri: str
    token: str
    is_active: bool

class _Token(BaseModel):
    access_token: str
    token_type: str

# -- A --

def authenticate_user(user_access_token: str):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(user_access_token, SECRET_KEY, algorithms=[ALGORITHM])
        uri: str = payload.get("sub")
        token: str = payload.get("token")
        if uri is None or token is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
    
    # check uri and token in db
    try:
        db_user = User.authenticate(uri == uri, token == token)
        return _User(uri=db_user.uri, token=db_user.token, is_active=db_user.is_active)
    except:
        return False

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

async def get_current_user(token: str = Depends(oauth2_cookie_scheme)):
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
        return _User(uri=db_user.uri, token=db_user.token, is_active=db_user.is_active)
    except:
        raise credentials_exception

async def check_authenticate_user(current_user: _User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return True

async def get_current_active_user(current_user: _User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# -- L --

async def login(form_data: OAuth2UserTokenRequestForm = Depends(), redicrect_url: str = "/"):
    
    user = authenticate_user(form_data.user_access_token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect user uri or token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_cookie_access_token(
        data={
            "sub": user.uri,
        }, 
        expires_delta=access_token_expires
    )
    
    token = jsonable_encoder(access_token)
    
    response = JSONResponse()
    response.set_cookie(
        "Authorization",
        value=f"Bearer {token}",
        httponly=True,
        max_age=COOKIE_MAX_AGE_SECONDS,
        expires=COOKIE_MAX_AGE_SECONDS,
    )
    return response

async def logout(current_user: _User, redicrect_url: str = "/"):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        User.unauthenticate(uri = current_user.uri)
        response = JSONResponse()
        response.delete_cookie("Authorization")
        return response
    except:
        raise credentials_exception

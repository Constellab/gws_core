# Core GWS app module
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import jwt

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import Response
from fastapi.param_functions import Form
from passlib.context import CryptContext
from pydantic import BaseModel

from gws.model import User
from gws.settings import Settings
from gws.central import Central
from gws._auth.central_api_key_header import oauth2_header_scheme

settings = Settings.retrieve()
SECRET_KEY = settings.data.get("secret_key")
ALGORITHM = "HS256"
CENTRAL_ACCESS_TOKEN_EXPIRE_MINUTES = 3

class _User(BaseModel):
    uri: str
    token: str
    is_active: bool



def check_api_key(api_key: str = Depends(oauth2_header_scheme)):
    if not Central.verify_api_key(api_key):
        raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
            )

# def central_origin(func):
#     def wrapper(*args, **kwargs):
#         print("xxxx")
#         print(kwargs)
#         check_api_key(*args, **kwargs)
#         return func(*args, **kwargs)
#     return wrapper

def get_user(user_uri:str):
    try:
        db_user = User.get(User.uri == user_uri)
        db_user.generate_access_token()
        return _User(uri=db_user.uri, token=db_user.token, is_active=db_user.is_active)
    except:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def generate_user_access_token(uri: str):
    user = get_user(uri)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authorized",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=CENTRAL_ACCESS_TOKEN_EXPIRE_MINUTES)

    access_token = create_access_token(
        data={
            "sub": user.uri,
            "token": user.token,
        }, 
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
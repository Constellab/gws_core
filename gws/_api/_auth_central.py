# Core GWS app module
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import jwt

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.param_functions import Form
from fastapi.requests import Request

from passlib.context import CryptContext

from fastapi.security import OAuth2PasswordRequestForm, OAuth2
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security.utils import get_authorization_scheme_param

from pydantic import BaseModel

from gws.model import User
from gws.settings import Settings
from gws.central import Central
from ._oauth2_central_header_scheme import oauth2_central_header_scheme

settings = Settings.retrieve()
SECRET_KEY = settings.data.get("secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60*24*3        # 3 days
COOKIE_MAX_AGE_SECONDS      = 60*60*24*3     # 3 days 


def check_central_api_key(api_key: str = Depends(oauth2_central_header_scheme)):
    is_authorized = Central.check_api_key(api_key)
    if not is_authorized:
        raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
            )
    
def get_user(user_uri:str):
    try:
        db_user = User.get(User.uri == user_uri)        
        from ._auth_user import UserData
        return UserData(
            uri = db_user.uri, 
            is_admin = db_user.is_admin, 
            is_active = db_user.is_active
        )
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

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.uri,
        }, 
        expires_delta=access_token_expires
    )
    
    content = {"access_token": access_token, "token_type": "bearer"}
    response = JSONResponse(content=content)
    response.set_cookie(
        "Authorization",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=COOKIE_MAX_AGE_SECONDS,
        expires=COOKIE_MAX_AGE_SECONDS,
    )
    
    return response
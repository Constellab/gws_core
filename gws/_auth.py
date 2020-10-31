# Core GWS app module
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.param_functions import Form
from passlib.context import CryptContext
from pydantic import BaseModel
import jwt

from gws.model import User
from gws.settings import Settings

settings = Settings.retrieve()

SECRET_KEY = settings.data.get("secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="handshake")

class _User(BaseModel):
    uri: str
    token: str
    is_active: bool

class _Token(BaseModel):
    access_token: str
    token_type: str

class _TokenData(BaseModel):
    uri: Optional[str] = None

def get_user(uri: str):
    db_user = User.get(User.uri == uri)
    return _User(uri=db_user.uri, token=db_user.token, is_active=db_user.is_active)

def authenticate_user(uri: str, token: str):
    db_user = User.authenticate(uri, token)
    return _User(uri=db_user.uri, token=db_user.token, is_active=db_user.is_active)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
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
        token_data = _TokenData(uri=uri)
    except Exception:
        raise credentials_exception
    user = get_user(uri=token_data.uri)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: _User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect user uri or token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.uri}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
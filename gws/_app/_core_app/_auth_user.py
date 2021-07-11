# Core GWS app module
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Optional
import jwt
from fastapi import Depends, HTTPException
from fastapi.param_functions import Form

from ...dto.user_dto import UserData
from ...user import User
from ...settings import Settings
from ...service.user_service import UserService
from ...exception.wrong_credentials_exception import WrongCredentialsException
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

# -- A --

# -- C --

async def check_user_access_token(token: str = Depends(oauth2_user_cookie_scheme))->UserData:
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        uri: str = payload.get("sub")
        if uri is None:
            raise WrongCredentialsException()
    except Exception:
        # -> An excpetion occured
        # -> Try to unauthenticate the current user
        from ...service.user_service import UserService
        try:
            user = UserService.get_current_user()
            if user:
                User.unauthenticate(uri=user.uri) 
        except:
            pass
        
        raise WrongCredentialsException()

    try:
        db_user = User.get(User.uri == uri)
        if not User.authenticate(uri=db_user.uri):
            raise WrongCredentialsException()
            
        return UserData(
            uri=db_user.uri, 
            email = db_user.email,
            first_name = db_user.first_name,
            last_name = db_user.last_name,
            group = db_user.group,
            is_active=db_user.is_active, 
            is_admin=db_user.is_admin,
            is_http_authenticated=db_user.is_http_authenticated,
            is_console_authenticated=db_user.is_console_authenticated
        )
    except Exception as err:
        print(err)
        raise WrongCredentialsException()


def check_is_sysuser():
    try:
        user = UserService.get_current_user()
    except:
        raise HTTPException(status_code=400, detail="Unauthorized: owner required")
        
    if not user.is_sysuser:
        raise HTTPException(status_code=400, detail="Unauthorized: owner required")
        
def check_is_owner():
    try:
        user = UserService.get_current_user()
    except:
        raise HTTPException(status_code=400, detail="Unauthorized: owner required")
        
    if not user.is_owner:
        raise HTTPException(status_code=400, detail="Unauthorized: owner required")
        
def check_is_admin():
    try:
        user = UserService.get_current_user()
    except:
        raise HTTPException(status_code=400, detail="Unauthorized: admin required")

    if not user.is_admin:
        raise HTTPException(status_code=400, detail="Unauthorized: admin required")
 

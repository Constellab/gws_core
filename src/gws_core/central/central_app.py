# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Dict, List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from starlette.exceptions import HTTPException

from gws_core.project.project_dto import CentralProject
from gws_core.project.project_service import ProjectService

from ..core.exception.exception_handler import ExceptionHandler
from ..core.service.settings_service import SettingsService
from ..core.utils.http_helper import HTTPHelper
from ..user.auth_service import AuthService
from ..user.user import User
from ..user.user_dto import UserData, UserLoginInfo
from ..user.user_service import UserService
from ._auth_central import AuthCentral

central_app = FastAPI(docs_url="/docs")


# Catch HTTP Exceptions
@central_app.exception_handler(HTTPException)
def all_http_exception_handler(request, exc):
    return ExceptionHandler.handle_exception(request, exc)

# Catch RequestValidationError (422 Unprocessable Entity)


@central_app.exception_handler(RequestValidationError)
def validation_exception_handler(request, exc: RequestValidationError):
    return ExceptionHandler.handle_request_validation_error(exc)


# Catch all other exceptions
@central_app.exception_handler(Exception)
def all_exception_handler(request, exc):
    return ExceptionHandler.handle_exception(request, exc)


##################################################### GLOBAL  #####################################################
@central_app.get("/settings", summary="Get settings")
def get_settings(_: UserData = Depends(AuthCentral.check_central_api_key)) -> dict:
    return SettingsService.get_settings().to_json()


@central_app.get("/health-check", summary="Health check route")
def health_check() -> bool:
    """
    Simple health check route
    """

    return True

# @central_app.get("/db/{db_manager_name}/dump", tags=["DB management"])
# def dump_db(db_manager_name: str, _: UserData = Depends(AuthCentral.check_central_api_key)):
#     output_file = MySQLService.dump_db(db_manager_name)
#     file = File()
#     file.path = output_file
#     FsNodeService.add_file_to_default_store(file, 'dump.sql')
#     return file.view_as_json().to_dict(ConfigParams())


##################################################### USER #####################################################


class TokenData(BaseModel):
    access_token: str
    token_type: str


class UserIdData(BaseModel):
    id: str


# ##################################################################
#
# User
#
# ##################################################################


@central_app.post("/user/generate-temp-access", tags=["User management"])
def generate_user_temp_access(user_login_info: UserLoginInfo,
                              _=Depends(AuthCentral.check_central_api_key_and_user)) -> dict:
    """
    Generate a temporary link for the user to login in the lab
    """

    return {"temp_token":  AuthService.generate_user_temp_access(user_login_info)}


@central_app.put("/user/{id}/activate", tags=["User management"])
def activate_user(id: str, _: UserData = Depends(AuthCentral.check_central_api_key_and_user)):
    """
    Activate a user. Requires central privilege.

    - **id**: the user id
    """

    return _convert_user_to_dto(UserService.activate_user(id))


@central_app.put("/user/{id}/deactivate", tags=["User management"])
def deactivate_user(id: str, _: UserData = Depends(AuthCentral.check_central_api_key_and_user)):
    """
    Deactivate a user. Require central privilege.

    - **id**: the user id
    """

    return _convert_user_to_dto(UserService.deactivate_user(id))


@central_app.get("/user/{id}", tags=["User management"])
def get_user(id: str, _: UserData = Depends(AuthCentral.check_central_api_key_and_user)):
    """
    Get the details of a user. Require central privilege.

    - **id**: the user id
    """

    return _convert_user_to_dto(UserService.get_user_by_id(id))


@central_app.post("/user", tags=["User management"])
def create_user(user: UserData, _: UserData = Depends(AuthCentral.check_central_api_key)):
    """
    Create a new user. Do not check the current user in this route because a user can created his own account.

    UserData:
    - **id**: The user id
    - **email**: The user emails
    - **group**: The user group. Valid groups are: **owner** (lab owner), **user** (user with normal privileges), **admin** (adminstrator).
    - **first_name**: The first names
    - **last_name**: The last name
    """

    return _convert_user_to_dto(UserService.create_central_user(user))


@central_app.get("/user", tags=["User management"])
def get_users(_: UserData = Depends(AuthCentral.check_central_api_key_and_user)):
    """
    Get the all the users. Require central privilege.
    """
    HTTPHelper.is_http_context()
    return _convert_users_to_dto(UserService.get_all_users())


def _convert_user_to_dto(user: User) -> Dict:
    if user is None:
        return None
    return {
        "id": user.id,
        "email": user.email,
        "group": user.group,
        "is_active": user.is_active,
        "first_name": user.first_name,
        "last_name": user.last_name
    }


def _convert_users_to_dto(users: List[User]) -> List[Dict]:
    return list(map(_convert_user_to_dto, users))


##################################################### PROJECT #####################################################

@central_app.post("/project", tags=["Project"])
def create_project(project: CentralProject, _: UserData = Depends(AuthCentral.check_central_api_key_and_user)):
    """
    Register a central project to the lab

    """

    return ProjectService.synchronize_central_project(project)


@central_app.delete("/project/{id}", tags=["Project"])
def delete_project(id: str, _: UserData = Depends(AuthCentral.check_central_api_key_and_user)):
    """
    Remove a project from the lab

    """

    return ProjectService.delete_project(id)

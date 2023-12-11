# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Dict, List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from starlette.exceptions import HTTPException

from gws_core.experiment.experiment_service import ExperimentService
from gws_core.lab.dev_env_service import DevEnvService
from gws_core.project.project_dto import SpaceProject
from gws_core.project.project_service import ProjectService
from gws_core.user.activity.activity_service import ActivityService

from ..core.exception.exception_handler import ExceptionHandler
from ..core.service.settings_service import SettingsService
from ..user.auth_service import AuthService
from ..user.user import User
from ..user.user_dto import UserFullDTO, UserLoginInfo
from ..user.user_service import UserService
from ._auth_space import AuthSpace

space_app = FastAPI(docs_url="/docs")


# Catch HTTP Exceptions
@space_app.exception_handler(HTTPException)
async def all_http_exception_handler(request, exc):
    return ExceptionHandler.handle_exception(request, exc)

# Catch RequestValidationError (422 Unprocessable Entity)


@space_app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    return ExceptionHandler.handle_request_validation_error(exc)


# Catch all other exceptions
@space_app.exception_handler(Exception)
async def all_exception_handler(request, exc):
    return ExceptionHandler.handle_exception(request, exc)


##################################################### GLOBAL  #####################################################
@space_app.get("/settings", summary="Get settings")
def get_settings(_=Depends(AuthSpace.check_space_api_key)) -> dict:
    return SettingsService.get_settings().to_json()


@space_app.get("/health-check", summary="Health check route")
def health_check() -> bool:
    """
    Simple health check route
    """

    return True
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


@space_app.post("/user/generate-temp-access", tags=["User management"])
def generate_user_temp_access(user_login_info: UserLoginInfo,
                              _=Depends(AuthSpace.check_space_api_key_and_user)) -> dict:
    """
    Generate a temporary link for the user to login in the lab
    """

    return {"temp_token":  AuthService.generate_user_temp_access(user_login_info)}


@space_app.put("/user/{id}/activate", tags=["User management"])
def activate_user(id: str, _=Depends(AuthSpace.check_space_api_key_and_user)):
    """
    Activate a user. Requires space privilege.

    - **id**: the user id
    """

    return _convert_user_to_dto(UserService.activate_user(id))


@space_app.put("/user/{id}/deactivate", tags=["User management"])
def deactivate_user(id: str, _=Depends(AuthSpace.check_space_api_key_and_user)):
    """
    Deactivate a user. Require space privilege.

    - **id**: the user id
    """

    return _convert_user_to_dto(UserService.deactivate_user(id))


@space_app.get("/user/{id}", tags=["User management"])
def get_user(id: str, _=Depends(AuthSpace.check_space_api_key_and_user)):
    """
    Get the details of a user. Require space privilege.

    - **id**: the user id
    """

    return _convert_user_to_dto(UserService.get_user_by_id(id))


@space_app.post("/user", tags=["User management"])
def create_user(user: UserFullDTO, _=Depends(AuthSpace.check_space_api_key)):
    """
    Create a new user.
    """

    return _convert_user_to_dto(UserService.create_or_update_user_dto(user))


@space_app.get("/user", tags=["User management"])
def get_users(_=Depends(AuthSpace.check_space_api_key_and_user)):
    """
    Get the all the users. Require space privilege.
    """
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

@space_app.post("/project", tags=["Project"])
def create_project(project: SpaceProject, _=Depends(AuthSpace.check_space_api_key_and_user)):
    """
    Register a space project to the lab

    """

    return ProjectService.synchronize_space_project(project)


@space_app.delete("/project/{id}", tags=["Project"])
def delete_project(id: str, _=Depends(AuthSpace.check_space_api_key_and_user)):
    """
    Remove a project from the lab

    """

    return ProjectService.delete_project(id)


############################################### EXPERIMENT #####################################################

@space_app.get("/lab/global-activity", tags=["Experiment"])
def lab_activity(_=Depends(AuthSpace.check_space_api_key)):
    """
    Count the number of running or queued experiments

    """

    last_activity = ActivityService.get_last_activity()

    return {
        "running_experiments": ExperimentService.count_running_or_queued_experiments(),
        "queued_experiments": ExperimentService.count_queued_experiments(),
        "last_activity": last_activity.to_json() if last_activity is not None else None,
        'dev_env_running': DevEnvService.dev_env_is_running()
    }

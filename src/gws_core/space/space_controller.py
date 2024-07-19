

from typing import List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.experiment.experiment_service import ExperimentService
from gws_core.lab.dev_env_service import DevEnvService
from gws_core.lab.system_dto import SettingsDTO
from gws_core.project.project_dto import SpaceProject
from gws_core.project.project_service import ProjectService
from gws_core.space.space_dto import LabActivityReponseDTO
from gws_core.user.activity.activity_service import ActivityService

from ..core.exception.exception_handler import ExceptionHandler
from ..core.service.settings_service import SettingsService
from ..user.auth_service import AuthService
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
def get_settings(_=Depends(AuthSpace.check_space_api_key)) -> SettingsDTO:
    return SettingsService.get_settings().to_dto()


@space_app.get("/health-check", summary="Health check route")
def health_check() -> bool:
    """
    Simple health check route
    """

    return True
##################################################### USER #####################################################


class TokenData(BaseModelDTO):
    access_token: str
    token_type: str


class UserIdData(BaseModelDTO):
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


@space_app.put("/user/{id_}/activate", tags=["User management"])
def activate_user(id_: str, _=Depends(AuthSpace.check_space_api_key_and_user)) -> UserFullDTO:
    """
    Activate a user. Requires space privilege.

    - **id_**: the user id_
    """

    return UserService.activate_user(id_).to_full_dto()


@space_app.put("/user/{id_}/deactivate", tags=["User management"])
def deactivate_user(id_: str, _=Depends(AuthSpace.check_space_api_key_and_user)) -> UserFullDTO:
    """
    Deactivate a user. Require space privilege.

    - **id_**: the user id_
    """

    return UserService.deactivate_user(id_).to_full_dto()


@space_app.get("/user/{id_}", tags=["User management"])
def get_user(id_: str, _=Depends(AuthSpace.check_space_api_key_and_user)) -> UserFullDTO:
    """
    Get the details of a user. Require space privilege.

    - **id_**: the user id_
    """

    return UserService.get_user_by_id(id_).to_full_dto()


@space_app.post("/user", tags=["User management"])
def create_user(user: UserFullDTO, _=Depends(AuthSpace.check_space_api_key)) -> UserFullDTO:
    """
    Create a new user.
    """

    return UserService.create_or_update_user_dto(user).to_full_dto()


@space_app.get("/user", tags=["User management"])
def get_users(_=Depends(AuthSpace.check_space_api_key_and_user)) -> List[UserFullDTO]:
    """
    Get the all the users. Require space privilege.
    """
    users = UserService.get_all_users()
    return [user.to_full_dto() for user in users]


##################################################### PROJECT #####################################################

@space_app.post("/project", tags=["Project"])
def create_project(project: SpaceProject, _=Depends(AuthSpace.check_space_api_key)) -> None:
    """
    Register a space project to the lab

    """

    ProjectService.synchronize_space_project(project)


@space_app.delete("/project/{id_}", tags=["Project"])
def delete_project(id_: str, _=Depends(AuthSpace.check_space_api_key)) -> None:
    """
    Remove a project from the lab

    """

    ProjectService.delete_project(id_)


############################################### EXPERIMENT #####################################################

@space_app.get("/lab/global-activity", tags=["Experiment"])
def lab_activity(_=Depends(AuthSpace.check_space_api_key)) -> LabActivityReponseDTO:
    """
    Count the number of running or queued experiments

    """

    last_activity = ActivityService.get_last_activity()

    return LabActivityReponseDTO(
        running_experiments=ExperimentService.count_running_or_queued_experiments(),
        queued_experiments=ExperimentService.count_queued_experiments(),
        last_activity=last_activity.to_dto() if last_activity is not None else None,
        dev_env_running=DevEnvService.dev_env_is_running()
    )

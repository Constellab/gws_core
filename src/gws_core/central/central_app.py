# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Any, Dict, List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse
from gws_core.config.config_types import ConfigParams
from gws_core.impl.file.file_helper import FileHelper
from gws_core.report.report_service import ReportService
from gws_core.resource.resource_service import ResourceService
from gws_core.resource.view.view_types import CallViewParams
from pydantic import BaseModel
from starlette.exceptions import HTTPException

from ..core.exception.exception_handler import ExceptionHandler
from ..core.service.mysql_service import MySQLService
from ..core.service.settings_service import SettingsService
from ..core.utils.http_helper import HTTPHelper
from ..impl.file.file import File
from ..impl.file.fs_node_service import FsNodeService
from ..user.auth_service import AuthService
from ..user.user import User
from ..user.user_dto import UserCentral, UserData
from ..user.user_service import UserService
from ._auth_central import AuthCentral

central_app = FastAPI(docs_url="/docs")


# Catch HTTP Exceptions
@central_app.exception_handler(HTTPException)
async def allg_exception_handler(request, exc):
    return ExceptionHandler.handle_exception(request, exc)

# Catch RequestValidationError (422 Unprocessable Entity)


@central_app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    return ExceptionHandler.handle_request_validation_error(exc)


# Catch all other exceptions
@central_app.exception_handler(Exception)
async def all_exception_handler(request, exc):
    return ExceptionHandler.handle_exception(request, exc)


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
def generate_user_temp_access(user_central: UserCentral,
                              _=Depends(AuthCentral.check_central_api_key)) -> str:
    """
    Generate a temporary link for the user to login in the lab
    """

    return {"temp_token":  AuthService.generate_user_temp_access(user_central)}


@central_app.get("/user/{id}/activate", tags=["User management"])
def activate_user(id: str, _: UserData = Depends(AuthCentral.check_central_api_key)):
    """
    Activate a user. Requires central privilege.

    - **id**: the user id
    """

    return _convert_user_to_dto(UserService.activate_user(id))


@central_app.get("/user/{id}/deactivate", tags=["User management"])
def deactivate_user(id: str, _: UserData = Depends(AuthCentral.check_central_api_key)):
    """
    Deactivate a user. Require central privilege.

    - **id**: the user id
    """

    return _convert_user_to_dto(UserService.deactivate_user(id))


@central_app.get("/user/{id}", tags=["User management"])
def get_user(id: str, _: UserData = Depends(AuthCentral.check_central_api_key)):
    """
    Get the details of a user. Require central privilege.

    - **id**: the user id
    """

    return _convert_user_to_dto(UserService.get_user_by_id(id))


@central_app.post("/user", tags=["User management"])
def create_user(user: UserData, _: UserData = Depends(AuthCentral.check_central_api_key)):
    """
    Create a new user

    UserData:
    - **id**: The user id
    - **email**: The user emails
    - **group**: The user group. Valid groups are: **owner** (lab owner), **user** (user with normal privileges), **admin** (adminstrator).
    - **first_name**: The first names
    - **last_name**: The last name
    """

    return _convert_user_to_dto(UserService.create_user(user.dict()))


@central_app.get("/user", tags=["User management"])
def get_users(_: UserData = Depends(AuthCentral.check_central_api_key)):
    """
    Get the all the users. Require central privilege.
    """
    HTTPHelper.is_http_context()
    return _convert_users_to_dto(UserService.get_all_users())


@central_app.get("/settings", summary="Get settings")
async def get_settings(_: UserData = Depends(AuthCentral.check_central_api_key)) -> dict:
    return SettingsService.get_settings().to_json()


@central_app.get("/health-check", summary="Health check route")
async def health_check() -> bool:
    """
    Simple health check route
    """

    return True


@central_app.post("/resource/{id}/views/{view_name}", tags=["Resource"],
                  summary="Call the view name for a resource")
async def call_view_on_resource(id: str,
                                view_name: str,
                                call_view_params: CallViewParams,
                                _: UserData = Depends(AuthCentral.check_central_api_key)) -> Any:
    view_dict = await ResourceService.get_and_call_view_on_resource_model(id, view_name, call_view_params["values"],
                                                                          call_view_params["transformers"],
                                                                          call_view_params["save_view_config"])

    return view_dict


@central_app.get("/report/image/{filename}", tags=["Report"], summary="Get an object")
def get_image(filename: str,
              _: UserData = Depends(AuthCentral.check_central_api_key)) -> FileResponse:
    return ReportService.get_image_file_response(filename)


@central_app.get("/db/{db_manager_name}/dump", tags=["DB management"])
def dump_db(db_manager_name: str, _: UserData = Depends(AuthCentral.check_central_api_key)):
    output_file = MySQLService.dump_db(db_manager_name)
    file = File()
    file.path = output_file
    FsNodeService.add_file_to_default_store(file, 'dump.sql')
    return file.view_as_json().to_dict(ConfigParams())


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

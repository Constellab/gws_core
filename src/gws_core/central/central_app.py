# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Dict, List, Type

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.exceptions import HTTPException
from starlette_context.middleware import ContextMiddleware

from ..core.exception.exception_handler import ExceptionHandler
from ..core.exception.exceptions import BadRequestException, NotFoundException
from ..core.service.mysql_service import MySQLService
from ..core.utils.http_helper import HTTPHelper
from ..impl.file.file import File
from ..user.user import User
from ..user.user_dto import UserData
from ..user.user_service import UserService
from ._auth_central import check_central_api_key
from ._auth_central import \
    generate_user_access_token as _generate_user_access_token

central_app = FastAPI(docs_url="/docs")

# Enable core for the API
central_app.add_middleware(
    CORSMiddleware,
    allow_origin_regex="^(.*)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Catch all HTTP exceptions
@central_app.exception_handler(HTTPException)
async def allg_exception_handler(request, exc):
    return ExceptionHandler.handle_exception(exc)


# Catch all other exceptions
@central_app.exception_handler(Exception)
async def all_exception_handler(request, exc):
    return ExceptionHandler.handle_exception(exc)


central_app.add_middleware(
    ContextMiddleware
)


class TokenData(BaseModel):
    access_token: str
    token_type: str


class UserUriData(BaseModel):
    uri: str

# ##################################################################
#
# User
#
# ##################################################################


@central_app.post("/user/generate-access-token", response_model=TokenData, tags=["User management"])
async def generate_user_access_token(user_uri_data: UserUriData,
                                     _=Depends(check_central_api_key)):
    """
    Generate a temporary access token for a user.

    - **user_uri_data**: the user uri data (JSON string)

    For example:

    `
    curl -X "POST" \
      "${LAB_URL}/central-api/user/generate-access-token" \
      -H "Accept: application/json" \
      -H "Authorization: api-key ${API_KEY}" \
      -H "Content-Type: application/json" \
      -d "{\"uri\": \"${URI}\"}"
    `
    """

    return await _generate_user_access_token(user_uri_data.uri)


@central_app.get("/user/test", tags=["User management"])
async def get_user_test():
    """
    Testing API user details
    """

    return {
        "owner": {
            "uri": UserService.get_owner().uri,
        },
        "sys": {
            "uri": UserService.get_sysuser().uri,
        }
    }


@ central_app.get("/user/{uri}/activate", tags=["User management"])
async def activate_user(uri: str, _: UserData = Depends(check_central_api_key)):
    """
    Activate a user. Requires central privilege.

    - **uri**: the user uri
    """

    try:
        return __convert_user_to_dto(UserService.activate_user(uri))
    except Exception as err:
        raise BadRequestException(
            "Cannot activate the user") from err


@ central_app.get("/user/{uri}/deactivate", tags=["User management"])
async def deactivate_user(uri: str, _: UserData = Depends(check_central_api_key)):
    """
    Deactivate a user. Require central privilege.

    - **uri**: the user uri
    """

    try:
        return __convert_user_to_dto(UserService.deactivate_user(uri))
    except Exception as err:
        raise BadRequestException(
            "Cannot deactivate the user.") from err


@ central_app.get("/user/{uri}", tags=["User management"])
async def get_user(uri: str, _: UserData = Depends(check_central_api_key)):
    """
    Get the details of a user. Require central privilege.

    - **uri**: the user uri
    """

    try:
        return __convert_user_to_dto(UserService.get_user_by_uri(uri))
    except Exception as err:
        raise NotFoundException(
            "Cannot get the user.") from err


@ central_app.post("/user", tags=["User management"])
async def create_user(user: UserData, _: UserData = Depends(check_central_api_key)):
    """
    Create a new user

    UserData:
    - **uri**: The user uri
    - **email**: The user emails
    - **group**: The user group. Valid groups are: **owner** (lab owner), **user** (user with normal privileges), **admin** (adminstrator).
    - **first_name**: The first names
    - **last_name**: The last name
    """

    try:
        return __convert_user_to_dto(UserService.create_user(user.dict()))
    except Exception as err:
        raise BadRequestException(
            "Cannot create the user.") from err


@ central_app.get("/user", tags=["User management"])
async def get_users(_: UserData = Depends(check_central_api_key)):
    """
    Get the all the users. Require central privilege.
    """
    try:
        HTTPHelper.is_http_context()
        return __convert_users_to_dto(UserService.get_all_users())
    except Exception as err:
        raise NotFoundException(
            "Cannot get the users.") from err


@ central_app.get("/db/{db_name}/dump", tags=["DB management"])
async def dump_db(db_name: str, _: UserData = Depends(check_central_api_key)):
    output_file = MySQLService.dump_db(db_name)
    file = File(path=output_file)
    file.move_to_default_store()
    return file.to_json()


def __convert_user_to_dto(user: User) -> Dict:
    if user is None:
        return None
    return {
        "uri": user.uri,
        "email": user.email,
        "group": user.group,
        "is_active": user.is_active,
        "first_name": user.data["first_name"],
        "last_name": user.data["last_name"]
    }


def __convert_users_to_dto(users: List[User]) -> List[Dict]:
    return list(map(__convert_user_to_dto, users))

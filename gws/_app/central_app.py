# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, Dict, List

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette_context.middleware import ContextMiddleware

from gws.http import *
from gws.model import User

from ._core_app._auth_user import UserData
from ._central_app._auth_central import check_central_api_key
from ._central_app._auth_central import generate_user_access_token as _generate_user_access_token

central_app = FastAPI(docs_url="/docs")

# Enable core for the API
central_app.add_middleware(
    CORSMiddleware,
    allow_origin_regex="^(.*)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@central_app.post("/user", tags=["User management"])
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

    from gws.service.user_service import UserService

    try:
        return __convert_user_to_dto(UserService.create_user(user.dict()))
    except Exception as err:
        raise HTTPInternalServerError(detail=f"Cannot create the user. Error: {err}")


@central_app.get("/user/test", tags=["User management"])
async def get_user_test():
    """
    Testing API user details
    """

    from gws.model import User
    return {
        "owner": {
            "uri": User.get_owner().uri,
        },
        "sys": {
            "uri": User.get_sysuser().uri,
        }
    }

@central_app.get("/user/list", tags=["User management"])
async def get_user_list(page: int = 1, \
                        number_of_items_per_page: int = 20, \
                       _: UserData = Depends(check_central_api_key)):
    """
    Retrieve the list of users. Requires central privilege.

    - **page**: the page number
    - **number_of_items_per_page**: the number of items per page. Defaults to 20 items per page.
    """

    try:
        user: User = UserService.get_user_by_uri(uri)
        return __convert_user_to_dto(user)
    except Exception as err:
        raise HTTPInternalServerError(
            detail=f"Cannot get the user. Error: {err}")


@app.get("/user", tags=["User management"])
async def get_users(_: UserData = Depends(check_central_api_key)):
    """
    Get the all the users. Require central privilege.
    """
    try:
        return UserService.fetch_user_list(page=page, number_of_items_per_page=number_of_items_per_page)
    except Exception as err:
        raise HTTPInternalServerError(detail=f"Cannot get the user. Error: {err}")

@central_app.get("/user/{uri}/activate", tags=["User management"])
async def activate_user(uri: str, _: UserData = Depends(check_central_api_key)):
    """
    Activate a user. Requires central privilege.

    - **uri**: the user uri
    """

    from gws.service.user_service import UserService

    try:
        return UserService.activate_user(uri)
    except Exception as err:
        raise HTTPInternalServerError(detail=f"Cannot activate the user. Error: {err}")


@central_app.get("/user/{uri}/deactivate", tags=["User management"])
async def deactivate_user(uri: str, _: UserData = Depends(check_central_api_key)):
    """
    Deactivate a user. Require central privilege.

    - **uri**: the user uri
    """

    from gws.service.user_service import UserService

    try:
        return UserService.deactivate_user(uri)
    except Exception as err:
        raise HTTPInternalServerError(detail=f"Cannot deactivate the user. Error: {err}")

    @app.get("/user/{uri}", tags=["User management"])
    async def get_user(uri: str, _: UserData = Depends(check_central_api_key)):
        """
        Get the details of a user. Require central privilege.

        - **uri**: the user uri
        """

        try:
            return __convert_user_to_dto(UserService.get_user_by_uri(uri))
        except Exception as err:
            raise HTTPInternalServerError(
                detail=f"Cannot get the user. Error: {err}")

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

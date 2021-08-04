# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, Coroutine, Optional

from fastapi import Cookie, Depends, Header
from starlette.responses import JSONResponse

from ..core.exception.exceptions import UnauthorizedException
from ..core.exception.gws_exceptions import GWSException
from ..core_app import core_app
from ..user.auth_service import AuthService
from .credentials_dto import CredentialsDTO
from .user_dto import UserData
from .user_service import UserService


@core_app.get("/user/me", response_model=UserData, tags=["User"])
async def read_user_me(current_user: UserData = Depends(AuthService.check_user_access_token)):
    """
    Get current user details.
    """

    return current_user


@core_app.get("/user/activity", tags=["User"], summary="Get user activities")
async def get_user_activity(user_uri: Optional[str] = None,
                            activity_type: Optional[str] = None,
                            page: int = 1,
                            number_of_items_per_page: int = 20,
                            _: UserData = Depends(AuthService.check_user_access_token)):
    """
    Get the list of user activities on the lab

    - **user_uri**: the uri the user [optional]
    - **activity_type**: the type of the activity to retrieve [optional]. The valid types of activities are:
      - **CREATE** : the creation of an object
      - **SAVE**   : the saving of an object
      - **START**  : the start of an experiment
      - **STOP**   : the stop of an experiment
      - **DELETE** : the deletion of an experiment
      - **ARCHIVE** : the archive of an object
      - **VALIDATE** : the valdaition of an experiment
      - **HTTP_AUTHENTICATION** : HTTP authentication
      - **HTTP_UNAUTHENTICATION** : HTTP unauthentication
      - **CONSOLE_AUTHENTICATION** : console authentication (through CLI or notebook)
      - **CONSOLE_UNAUTHENTICATION** : console unauthentication
    - **page**: the page number
    - **number_of_items_per_page**: the number of items per page. Defaults to 20 items per page.
    """

    return UserService.fecth_activity_list(
        user_uri=user_uri,
        activity_type=activity_type,
        page=page,
        number_of_items_per_page=number_of_items_per_page,
        as_json=True
    )


@core_app.post("/login", tags=["User"], summary="Login to the lab by requesting central")
async def login(credentials: CredentialsDTO) -> Coroutine[Any, Any, JSONResponse]:
    """
    Log the user using central
    """

    return await AuthService.login(credentials)


@core_app.post("/dev-login", tags=["User"], summary="Login to the dev lab using the prod token")
async def dev_login(authorization_header: Optional[str] = Header(default=None, alias="Authorization"),
                    authorization_cookie: Optional[str] = Cookie(default=None, alias="Authorization")) -> Coroutine[Any, Any, JSONResponse]:
    """
    Log the user on the dev lab by calling the prod api
    """
    # get the token from the header or the cookies
    token: str = authorization_header or authorization_cookie

    if token is None:
        raise UnauthorizedException(detail=GWSException.WRONG_CREDENTIALS.value,
                                    unique_code=GWSException.WRONG_CREDENTIALS.name)

    return await AuthService.dev_login(token)


@core_app.get("/check-token", tags=["User"], summary="Check user's token")
def check_token(current_user: UserData = Depends(AuthService.check_user_access_token)) -> str:
    """Simple route to check the user's token (used in automatique dev login), returns the user's uri if valid
    """
    return current_user.uri

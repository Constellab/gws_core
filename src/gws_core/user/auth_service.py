

from typing import Any, Coroutine

from fastapi.param_functions import Depends
from requests.models import Response
from starlette.responses import JSONResponse

from ..central.central_service import CentralService
from ..core.exception.exceptions import (BadRequestException,
                                         UnauthorizedException)
from ..core.exception.gws_exceptions import GWSException
from ..core.service.base_service import BaseService
from ..core.service.external_api_service import ExternalApiService
from ..core.utils.http_helper import HTTPHelper
from ..core.utils.logger import Logger
from ..core.utils.settings import Settings
from .activity import Activity
from .activity_service import ActivityService
from .credentials_dto import CredentialsDTO
from .current_user_service import CurrentUserService
from .invalid_token_exception import InvalidTokenException
from .jwt_service import JWTService
from .oauth2_user_cookie_scheme import oauth2_user_cookie_scheme
from .user import User
from .user_dto import UserData, UserDataDict
from .user_service import UserService
from .wrong_credentials_exception import WrongCredentialsException


class AuthService(BaseService):

    @classmethod
    def login(cls, credentials: CredentialsDTO) -> JSONResponse:

        # Check if user exist in the lab
        user: User = UserService.get_user_by_email(credentials.email)
        if user is None:
            raise WrongCredentialsException()

        # Check the user credentials
        credentials_valid: bool = CentralService.check_credentials(credentials)
        if not credentials_valid:
            raise WrongCredentialsException()

        return cls.generate_user_access_token(user.uri)

    @classmethod
    def generate_user_access_token(cls, uri: str) -> JSONResponse:
        user: User = UserService.fetch_user(uri)
        if not user:
            raise UnauthorizedException(
                detail=GWSException.WRONG_CREDENTIALS_USER_NOT_FOUND.value,
                unique_code=GWSException.WRONG_CREDENTIALS_USER_NOT_FOUND.name,
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise UnauthorizedException(
                detail=GWSException.WRONG_CREDENTIALS_USER_NOT_ACTIVATED.value,
                unique_code=GWSException.WRONG_CREDENTIALS_USER_NOT_ACTIVATED.name,
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = JWTService.create_jwt(user_uri=user.uri)

        content = {"access_token": access_token, "token_type": "bearer"}
        response = JSONResponse(content=content)

        # Add the token is the cookies
        response.set_cookie(
            "Authorization",
            value=f"Bearer {access_token}",
            httponly=True,
            max_age=JWTService.get_token_duration_in_seconds(),
            expires=JWTService.get_token_duration_in_seconds(),
        )

        return response

    @classmethod
    async def check_user_access_token(cls, token: str = Depends(oauth2_user_cookie_scheme)) -> UserData:

        try:
            user_uri: str = JWTService.check_user_access_token(token)

            db_user = User.get(User.uri == user_uri)
            if not cls.authenticate(uri=db_user.uri):
                raise InvalidTokenException()

            return UserData(
                uri=db_user.uri,
                email=db_user.email,
                first_name=db_user.first_name,
                last_name=db_user.last_name,
                group=db_user.group,
                is_active=db_user.is_active,
                is_admin=db_user.is_admin,
                is_http_authenticated=db_user.is_http_authenticated,
                is_console_authenticated=db_user.is_console_authenticated
            )
        except Exception:
            raise WrongCredentialsException()

    @classmethod
    def authenticate(cls, uri: str, console_token: str = "") -> bool:
        """
        Authenticate a user

        :param uri: The uri of the user to authenticate
        :type uri: `str`
        :param console_token: The console token. This token is only used if the for console contexts
        :type console_token: `str`
        :return: True if the user is successfully autheticated, False otherwise
        :rtype: `bool`
        """
        try:
            user = User.get(User.uri == uri)
        except Exception as err:
            raise BadRequestException(
                f"User not found with uri {uri}") from err
        if not user.is_active:
            return False
        if HTTPHelper.is_http_context():
            return cls.__authenticate_http(user)
        else:
            return cls.__authenticate_console(user, console_token)

    @classmethod
    def __authenticate_console(cls, user: User, console_token) -> bool:

        if user.is_console_authenticated:
            CurrentUserService.set_current_user(user)
            return True
        is_valid_token = bool(console_token) and (
            user.console_token == console_token)
        if not is_valid_token:
            return False

        with User.get_db_manager().db.atomic() as transaction:
            try:
                # authenticate the user first
                user.is_console_authenticated = True
                if user.save():
                    CurrentUserService.set_current_user(user)
                else:
                    raise BadRequestException("Cannot save user status")
                # now save user activity
                ActivityService.add(Activity.CONSOLE_AUTHENTICATION)
                return True
            except Exception as err:
                Logger.warning(f"User __authenticate_console {err}")
                transaction.rollback()
                return False

    @classmethod
    def __authenticate_http(cls, user: User) -> bool:

        if user.is_http_authenticated:
            CurrentUserService.set_current_user(user)
            return True
        with User.get_db_manager().db.atomic() as transaction:
            try:
                # authenticate the user first
                user.is_http_authenticated = True
                if user.save():
                    CurrentUserService.set_current_user(user)
                else:
                    raise BadRequestException("Cannot save user status")
                # now save user activity
                ActivityService.add(Activity.HTTP_AUTHENTICATION)
                return True
            except Exception as err:
                Logger.warning(f"User __authenticate_http {err}")
                transaction.rollback()
                return False

    @classmethod
    def unauthenticate(cls, uri: str) -> bool:
        """
        Unauthenticate a user

        :param uri: The uri of the user to unauthenticate
        :type uri: `str`
        :return: True if the user is successfully unautheticated, False otherwise
        :rtype: `bool`
        """
        try:
            user = User.get(User.uri == uri)
        except Exception as err:
            raise BadRequestException(
                f"User not found with uri {uri}") from err
        if not user.is_active:
            return False
        if HTTPHelper.is_http_context():
            return cls.__unauthenticate_http(user)
        else:
            return cls.__unauthenticate_console(user)

    @classmethod
    def dev_login(cls, token: str) -> Coroutine[Any, Any, str]:
        """[summary]
        Log the user on the dev lab by calling the prod api
        Only allowed for the dev service

        It check the user's prod token by calling the prod api and if it's valid, it
        generate a token for the development environment

        :param credentials: [description]
        :type credentials: CredentialsDTO
        :raises WrongCredentialsException: [description]
        :raises WrongCredentialsException: [description]
        :return: [description]
        :rtype: Coroutine[Any, Any, str]
        """

        settings: Settings = Settings.retrieve()

        # Allow only this method on dev environment
        if settings.is_prod:
            raise BadRequestException(detail=GWSException.FUNCTIONALITY_UNAVAILBLE_IN_PROD.value,
                                      unique_code=GWSException.FUNCTIONALITY_UNAVAILBLE_IN_PROD.name)

        # retrieve the prod api url
        prod_api_url: str = settings.get_prod_api_url()

        if prod_api_url is None:
            raise BadRequestException(detail=GWSException.MISSING_PROD_API_URL.value,
                                      unique_code=GWSException.MISSING_PROD_API_URL.name)

        # Check if the user's token is valid in prod environment and retrieve user's information
        try:
            response: Response = ExternalApiService.get(
                url=f"{prod_api_url}/core-api/user/me", headers={"Authorization": token})
        except Exception as err:
            Logger.error(
                f"Error during authentication to the prod api : {err}")
            raise BadRequestException(detail=GWSException.ERROR_DURING_DEV_LOGIN.value,
                                      unique_code=GWSException.ERROR_DURING_DEV_LOGIN.name)

        if response.status_code != 200:
            raise BadRequestException(detail=GWSException.ERROR_DURING_DEV_LOGIN.value,
                                      unique_code=GWSException.ERROR_DURING_DEV_LOGIN.name)
        # retrieve the user from the response
        user: UserDataDict = response.json()

        if not user["is_active"]:
            raise BadRequestException(detail=GWSException.USER_NOT_ACTIVATED.value,
                                      unique_code=GWSException.USER_NOT_ACTIVATED.name)

        userdb: User = UserService.create_user_if_not_exists(user)

        # The user's prod token is valid, we can return the token for the development environment
        return cls.generate_user_access_token(userdb.uri)

    @classmethod
    def __unauthenticate_http(cls, user: User) -> bool:

        if not user.is_http_authenticated:
            CurrentUserService.set_current_user(None)
            return True
        with User.get_db_manager().db.atomic() as transaction:
            try:
                user.is_http_authenticated = False
                ActivityService.add(Activity.HTTP_UNAUTHENTICATION)
                if user.save():
                    CurrentUserService.set_current_user(None)
                else:
                    raise BadRequestException("Cannot save user status")
                return True
            except Exception as err:
                Logger.warning(f"User __unauthenticate_http {err}")
                transaction.rollback()
                return False

    @classmethod
    def __unauthenticate_console(cls, user: User) -> bool:

        if not user.is_console_authenticated:
            CurrentUserService.set_current_user(None)
            return True
        with User.get_db_manager().db.atomic() as transaction:
            try:
                user.is_console_authenticated = False
                ActivityService.add(Activity.CONSOLE_UNAUTHENTICATION)
                if user.save():
                    CurrentUserService.set_current_user(None)
                else:
                    raise BadRequestException("Cannot save user status")
                return True
            except Exception as err:
                Logger.warning(f"User __unauthenticate_console {err}")
                transaction.rollback()
                return False

    @classmethod
    def check_is_sysuser(cls):
        try:
            user = CurrentUserService.get_and_check_current_user()
        except:
            raise UnauthorizedException(detail="Unauthorized: owner required")

        if not user.is_sysuser:
            raise UnauthorizedException(detail="Unauthorized: owner required")

    @classmethod
    def check_is_owner(cls):
        try:
            user = CurrentUserService.get_and_check_current_user()
        except:
            raise UnauthorizedException(detail="Unauthorized: owner required")

        if not user.is_owner:
            raise UnauthorizedException(detail="Unauthorized: owner required")

    @classmethod
    def check_is_admin(cls):
        try:
            user = CurrentUserService.get_and_check_current_user()
        except:
            raise UnauthorizedException(detail="Unauthorized: admin required")

        if not user.is_admin:
            raise UnauthorizedException(detail="Unauthorized: admin required")

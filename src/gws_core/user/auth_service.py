

from typing import Any, Coroutine, Union

import jwt
from fastapi import Depends
from starlette.responses import JSONResponse

from ..central._auth_central import generate_user_access_token
from ..central.central_service import CentralService
from ..core.exception import BadRequestException, UnauthorizedException
from ..core.service.base_service import BaseService
from ..core.service.http_service import HTTPService
from ..core.utils.logger import Logger
from ..core.utils.settings import Settings
from .activity import Activity
from .activity_service import ActivityService
from .credentials_dto import CredentialsDTO
from .current_user_service import CurrentUserService
from .oauth2_user_cookie_scheme import oauth2_user_cookie_scheme
from .user import User
from .user_dto import UserData
from .user_service import UserService
from .wrong_credentials_exception import WrongCredentialsException

settings = Settings.retrieve()
SECRET_KEY = settings.data.get("secret_key")
ALGORITHM = "HS256"


class AuthService(BaseService):

    @classmethod
    async def login(cls, credentials: CredentialsDTO) -> Coroutine[Any, Any, JSONResponse]:

        # Check if user exist in the lab
        user: User = UserService.get_user_by_email(credentials.email)
        if user is None:
            raise WrongCredentialsException()

        # Check the user credentials
        credentials_valid: bool = CentralService.check_credentials(credentials)
        if not credentials_valid:
            raise WrongCredentialsException()

        return await generate_user_access_token(user.uri)

    @classmethod
    async def check_user_access_token(cls, token: str = Depends(oauth2_user_cookie_scheme)) -> UserData:

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            uri: str = payload.get("sub")
            if uri is None:
                raise WrongCredentialsException()
        except Exception:
            # -> An excpetion occured
            # -> Try to unauthenticate the current user
            try:
                user = CurrentUserService.get_current_user()
                if user:
                    cls.unauthenticate(uri=user.uri)
            except:
                pass

            raise WrongCredentialsException()

        try:
            db_user = User.get(User.uri == uri)
            if not cls.authenticate(uri=db_user.uri):
                raise WrongCredentialsException()

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
        if HTTPService.is_http_context():
            return cls.__authenticate_http(user)
        else:
            return cls.__authenticate_console(user, console_token)

    @classmethod
    def __authenticate_console(cls, user, console_token) -> bool:

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
    def __authenticate_http(cls, user) -> bool:

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
        if HTTPService.is_http_context():
            return cls.__unauthenticate_http(user)
        else:
            return cls.__unauthenticate_console(user)

    @classmethod
    def __unauthenticate_http(cls, user) -> bool:
        from .activity import Activity

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
    def __unauthenticate_console(cls, user) -> bool:
        from .activity import Activity

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
            user = CurrentUserService.get_current_user()
        except:
            raise UnauthorizedException(detail="Unauthorized: owner required")

        if not user.is_sysuser:
            raise UnauthorizedException(detail="Unauthorized: owner required")

    @classmethod
    def check_is_owner(cls):
        try:
            user = CurrentUserService.get_current_user()
        except:
            raise UnauthorizedException(detail="Unauthorized: owner required")

        if not user.is_owner:
            raise UnauthorizedException(detail="Unauthorized: owner required")

    @classmethod
    def check_is_admin(cls):
        try:
            user = CurrentUserService.get_current_user()
        except:
            raise UnauthorizedException(detail="Unauthorized: admin required")

        if not user.is_admin:
            raise UnauthorizedException(detail="Unauthorized: admin required")

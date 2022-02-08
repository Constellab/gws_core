# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from fastapi.param_functions import Depends
from pydantic import JsonError
from requests.models import Response
from starlette.responses import JSONResponse

from ..central.central_service import CentralService
from ..core.exception.exceptions import (BadRequestException,
                                         UnauthorizedException)
from ..core.exception.gws_exceptions import GWSException
from ..core.service.base_service import BaseService
from ..core.service.external_api_service import ExternalApiService
from ..core.utils.logger import Logger
from ..core.utils.settings import Settings
from .activity import Activity
from .activity_service import ActivityService
from .credentials_dto import CredentialsDTO
from .current_user_service import CurrentUserService
from .jwt_service import JWTService
from .oauth2_user_cookie_scheme import oauth2_user_cookie_scheme
from .unique_code_service import (CodeObject, InvalidUniqueCodeException,
                                  UniqueCodeService)
from .user import User, UserDataDict
from .user_dto import UserCentral, UserData
from .user_exception import InvalidTokenException, WrongCredentialsException
from .user_service import UserService


class AuthService(BaseService):

    @classmethod
    def login(cls, credentials: CredentialsDTO) -> JSONResponse:

        # Check if user exist in the lab
        user: User

        try:
            user = UserService.get_user_by_email(credentials.email)
        except:
            raise WrongCredentialsException()

        # skip the check with central in local env
        if not Settings.is_local_env():
            # Check the user credentials
            credentials_valid: bool = CentralService.check_credentials(credentials)
            if not credentials_valid:
                raise WrongCredentialsException()

        # now save user activity
        ActivityService.add(Activity.HTTP_AUTHENTICATION, object_type=User._typing_name, object_id=user.id, user=user)

        return cls.generate_user_access_token(user.id)

    @classmethod
    def generate_user_access_token(cls, id: str) -> JSONResponse:
        user: User = UserService.fetch_user(id)
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

        access_token = JWTService.create_jwt(user_id=user.id)

        content = {"expiresIn": JWTService.get_token_duration_in_seconds()}
        response = JSONResponse(content=content)

        # Add the token is the cookies
        cls._set_token_in_response(access_token, JWTService.get_token_duration_in_seconds(), response)

        return response

    @classmethod
    def generate_user_temp_access(cls, user_central: UserCentral) -> str:
        user: User = UserService.fetch_user(user_central.id)
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

        # update the user info and save it
        user.first_name = user_central.firstname
        user.last_name = user_central.lastname
        user.email = user_central.email
        user.theme = user_central.theme
        user.save()

        return UniqueCodeService.generate_code(user.id, {})

    @classmethod
    def check_user_access_token(cls, token: str = Depends(oauth2_user_cookie_scheme)) -> UserData:

        try:
            user_id: str = JWTService.check_user_access_token(token)

            db_user: User = cls.authenticate(user_id)

            return UserData(
                id=db_user.id,
                email=db_user.email,
                first_name=db_user.first_name,
                last_name=db_user.last_name,
                group=db_user.group,
                is_active=db_user.is_active,
                is_admin=db_user.is_admin,
            )
        except Exception:
            raise InvalidTokenException()

    @classmethod
    def check_unique_code(cls, unique_code: str) -> UserData:
        """Use link the the token to check access for a unique code generated. return the object associated with the code
        """
        try:
            code_obj: CodeObject = UniqueCodeService.check_code(unique_code)

            cls.authenticate(code_obj["user_id"])

            return code_obj['obj']
        except Exception:
            raise InvalidUniqueCodeException()

    @classmethod
    def authenticate(cls, id: str) -> User:
        """
        Authenticate a user. Return the DB user if ok, throw an exception if not ok

        :param id: The id of the user to authenticate
        :type id: `str`
        """
        user: User = User.get_by_id_and_check(id)

        if not user.is_active:
            raise UnauthorizedException(
                detail=GWSException.WRONG_CREDENTIALS_USER_NOT_ACTIVATED.value,
                unique_code=GWSException.WRONG_CREDENTIALS_USER_NOT_ACTIVATED.name,
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Set the user in the context
        CurrentUserService.set_current_user(user)
        return user

    @classmethod
    def dev_get_check_user(cls, token: str) -> User:
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
        prod_api_url: str = settings.get_lab_prod_api_url()

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

        return UserService.create_user_if_not_exists(user)

    @classmethod
    def logout(cls) -> JSONResponse:
        response = JSONResponse(content={})
        cls._set_token_in_response('', 0, response)
        return response

    @classmethod
    def _set_token_in_response(cls, token: str, expireInSeconds: int, response: JSONResponse) -> None:
        # Add the token is the cookies
        response.set_cookie(
            "Authorization",
            value=token,
            httponly=True,
            max_age=expireInSeconds,
            expires=expireInSeconds,
            domain=Settings.get_virtual_host(),  # set the domain to virtual host so cookie works for dev and prod env,
            secure=not Settings.is_local_env(),
            # samesite='strict'
        )

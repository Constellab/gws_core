from gws_core.lab.system_service import SystemService
from gws_core.user.activity.activity_dto import ActivityObjectType, ActivityType
from starlette.responses import JSONResponse, Response

from ..core.exception.exceptions import UnauthorizedException
from ..core.exception.gws_exceptions import GWSException
from ..core.utils.settings import Settings
from ..space.space_service import ExternalCheckCredentialResponse, SpaceService
from .activity.activity_service import ActivityService
from .jwt_service import JWTService
from .unique_code_service import UniqueCodeService
from .user import User
from .user_credentials_dto import UserCredentials2Fa, UserCredentialsDTO
from .user_dto import UserLoginInfo, UserSpace
from .user_exception import WrongCredentialsException
from .user_service import UserService


class AuthenticationService:
    """Service for handling user authentication (login, logout)"""

    @classmethod
    def login(cls, credentials: UserCredentialsDTO) -> Response:
        # Check if user exist in the lab
        user: User

        try:
            user = UserService.get_user_by_email(credentials.email)
        except:
            raise WrongCredentialsException()

        # skip the check with space in local dev env
        if Settings.get_instance().is_local_dev_env():
            return cls.log_user(user)

        # Check the user credentials
        check_response: ExternalCheckCredentialResponse = (
            SpaceService.get_instance().check_credentials(credentials)
        )

        # if the user is logged
        if check_response.status == "OK":
            if check_response.user:
                cls.get_and_refresh_user_from_space(check_response.user)
            return cls.log_user(user)
        else:
            # if the user need to be logged with 2FA
            content = {"status": "2FA_REQUIRED", "twoFAUrlCode": check_response.twoFAUrlCode}
            return JSONResponse(content=content)

    @classmethod
    def login_with_2fa(cls, credentials: UserCredentials2Fa) -> Response:
        # Check if the code is valid
        user_space: UserSpace = SpaceService.get_instance().check_2_fa(credentials)

        # refresh and retrieve lab user
        user: User = cls.get_and_refresh_user_from_space(user_space)

        # Log the user
        return cls.log_user(user)

    @classmethod
    def log_user(cls, user: User, response: Response = None) -> Response:
        # now save user activity
        ActivityService.add(
            ActivityType.HTTP_AUTHENTICATION,
            object_type=ActivityObjectType.USER,
            object_id=user.id,
            user=user,
        )

        access_token = cls.generate_user_access_token(user.id)

        if response is None:
            content = {
                "status": "LOGGED_IN",
                "expiresIn": JWTService.get_token_duration_in_milliseconds(),
            }
            response = JSONResponse(content=content)

        # Add the token is the cookies
        cls.set_token_in_response(
            access_token, JWTService.get_token_duration_in_seconds(), response
        )

        return response

    @classmethod
    def generate_user_access_token(cls, id_: str) -> str:
        user: User = UserService.get_by_id_or_none(id_)
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

        return JWTService.create_jwt(user_id=user.id)

    @classmethod
    def generate_user_temp_access(cls, user_login_info: UserLoginInfo) -> str:
        user: User = cls.get_and_refresh_user_from_space(user_login_info.user)

        # refresh the space info
        SystemService.save_space_async(user_login_info.space)

        return UniqueCodeService.generate_code(user.id, {}, 60)

    @classmethod
    def get_and_refresh_user_from_space(cls, user_space: UserSpace) -> User:
        """Check user space exists in the lab and if yes, it updates the user info"""
        user: User = UserService.get_by_id_or_none(user_space.id)
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

        if (
            user.first_name != user_space.firstname
            or user.last_name != user_space.lastname
            or user.email != user_space.email
            or user.theme != user_space.theme
            or user.lang != user_space.lang
            or user.photo != user_space.photo
        ):
            # update the user info and save it
            user.first_name = user_space.firstname
            user.last_name = user_space.lastname
            user.email = user_space.email
            user.theme = user_space.theme
            user.lang = user_space.lang
            user.photo = user_space.photo
            user = user.save()

        return user

    @classmethod
    def logout(cls) -> JSONResponse:
        response = JSONResponse(content={})
        cls.set_token_in_response("", 0, response)
        return response

    @classmethod
    def set_token_in_response(cls, token: str, expire_in_seconds: int, response: Response) -> None:
        # Add the token is the cookies
        response.set_cookie(
            "Authorization",
            value=token,
            httponly=True,
            max_age=expire_in_seconds,
            expires=expire_in_seconds,
            secure=True,  # work only with https and localhost
            samesite="strict",
        )

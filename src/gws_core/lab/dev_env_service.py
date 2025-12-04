from requests.models import Response as ApiResponse
from starlette.responses import Response

from gws_core.core.exception.exceptions.bad_request_exception import BadRequestException
from gws_core.core.exception.gws_exceptions import GWSException
from gws_core.core.service.external_api_service import ExternalApiService
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.user.authentication_service import AuthenticationService
from gws_core.user.unique_code_service import UniqueCodeService
from gws_core.user.user import User
from gws_core.user.user_dto import UserFullDTO
from gws_core.user.user_service import UserService


class DevEnvService:
    @classmethod
    def dev_get_check_user(cls, unique_code: str) -> Response:
        """[summary]
        Log the user on the dev lab by calling the prod api
        Only allowed for the dev service

        It check the user's prod token by calling the prod api. If the token is valie,
        it create the user in the BD if not already there and return the user

        The dev environment uses the same token as the prod environment

        :param credentials: [description]
        :type credentials: CredentialsDTO
        :raises WrongCredentialsException: [description]
        :raises WrongCredentialsException: [description]
        :return: [description]
        """

        settings: Settings = Settings.get_instance()

        # Allow only this method on dev environment
        if settings.is_prod_mode():
            raise BadRequestException(
                detail=GWSException.FUNCTIONALITY_UNAVAILBLE_IN_PROD.value,
                unique_code=GWSException.FUNCTIONALITY_UNAVAILBLE_IN_PROD.name,
            )

        # retrieve the prod api url
        prod_api_url: str = settings.get_lab_prod_api_url()

        if prod_api_url is None:
            raise BadRequestException(
                detail=GWSException.MISSING_PROD_API_URL.value,
                unique_code=GWSException.MISSING_PROD_API_URL.name,
            )

        # Check if the user's token is valid in prod environment and retrieve user's information
        try:
            response: ApiResponse = ExternalApiService.post(
                url=f"{prod_api_url}/{Settings.core_api_route_path()}/dev-login-unique-code/check/{unique_code}",
                body=None,
            )
        except Exception as err:
            Logger.error(f"Error during authentication to the prod api : {err}")
            raise BadRequestException(
                detail=GWSException.ERROR_DURING_DEV_LOGIN.value,
                unique_code=GWSException.ERROR_DURING_DEV_LOGIN.name,
            )

        if response.status_code != 200:
            raise BadRequestException(
                detail=GWSException.ERROR_DURING_DEV_LOGIN.value,
                unique_code=GWSException.ERROR_DURING_DEV_LOGIN.name,
            )
        # retrieve the user from the response
        user_dto = UserFullDTO.from_json(response.json())

        if not user_dto.is_active:
            raise BadRequestException(
                detail=GWSException.USER_NOT_ACTIVATED.value,
                unique_code=GWSException.USER_NOT_ACTIVATED.name,
            )

        user: User = UserService.create_or_update_user_dto(user_dto)

        return AuthenticationService.log_user(user, Response())

    @classmethod
    def generate_dev_login_unique_code(cls, user_id: str) -> str:
        # generate a code available for 60 seconds
        return UniqueCodeService.generate_code(user_id, {}, 60)

    @classmethod
    def check_dev_login_unique_code(cls, unique_code: str) -> User:
        # check the unique code
        code_obj = UniqueCodeService.check_code(unique_code)

        # return the user associated with the code
        return User.get_by_id_and_check(code_obj.user_id)

    @classmethod
    def dev_env_is_running(cls) -> bool:
        if Settings.get_instance().is_dev_mode():
            return True

        dev_api = Settings.get_lab_dev_api_url()

        if not dev_api:
            return False

        try:
            ExternalApiService.get(
                dev_api + "/" + Settings.core_api_route_path() + "/health-check",
                raise_exception_if_error=True,
            )
            return True
        except Exception:
            return False

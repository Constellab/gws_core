import os
import tempfile
import time
from typing import cast

from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.exception.exceptions.base_http_exception import BaseHTTPException
from gws_core.core.service.external_api_service import ExternalApiService, FormData
from gws_core.core.utils.compress.zip_compress import ZipCompress
from gws_core.core.utils.date_helper import DateHelper
from gws_core.credentials.credentials import Credentials
from gws_core.credentials.credentials_service import CredentialsService
from gws_core.credentials.credentials_type import CredentialsDataBasic
from gws_core.docker.docker_dto import (
    RegisterComposeOptionsRequestDTO,
    RegisterSQLDBComposeAPIResponseDTO,
    RegisterSQLDBComposeRequestDTO,
    RegisterSQLDBComposeRequestOptionsDTO,
    RegisterSQLDBComposeResponseDTO,
    StartComposeRequestDTO,
    SubComposeListDTO,
    SubComposeStatusDTO,
)
from gws_core.docker.lab_manager_service_base import LabManagerServiceBase


class DockerService(LabManagerServiceBase):
    _DOCKER_ROUTE: str = "sub-compose"

    def register_and_start_compose(
        self,
        brick_name: str,
        unique_name: str,
        compose_yaml_content: str,
        options: RegisterComposeOptionsRequestDTO,
    ) -> None:
        """
        Start a docker compose from string content

        :param compose: The docker-compose content object
        :type compose: StartComposeRequestDTO
        :param brick_name: Name of the brick
        :type brick_name: str
        :param unique_name: Unique name for the compose
        :type unique_name: str
        :param compose_yaml_content: Content of the docker-compose YAML file
        :type compose_yaml_content: str
        :param options: Options for the compose registration
        :type options: RegisterComposeOptionsRequestDTO
        :return: Response containing message and output
        :rtype: DockerComposeResponseDTO
        """

        lab_api_url = self._get_lab_manager_api_url(
            f"{self._DOCKER_ROUTE}/{brick_name}/{unique_name}/register"
        )

        compose = StartComposeRequestDTO(
            compose_yaml_content=compose_yaml_content,
            options=options,
        )

        try:
            ExternalApiService.post(
                lab_api_url,
                compose,
                headers=self._get_request_header(),
                raise_exception_if_error=True,
            )

        except BaseHTTPException as err:
            err.detail = f"Can't start compose from string. Error: {err.detail}"
            raise err

    def register_sub_compose_from_folder(
        self,
        brick_name: str,
        unique_name: str,
        folder_path: str,
        options: RegisterComposeOptionsRequestDTO,
    ) -> None:
        """
        Register a docker compose from a folder by zipping it and uploading

        :param brick_name: Name of the brick
        :type brick_name: str
        :param unique_name: Unique name for the compose
        :type unique_name: str
        :param folder_path: Path to the folder containing the compose files
        :type folder_path: str
        :param options: Options for the compose registration
        :type options: RegisterComposeOptionsRequestDTO
        :return: Status information of the compose
        :rtype: DockerComposeStatusInfoDTO
        """

        lab_api_url = self._get_lab_manager_api_url(
            f"{self._DOCKER_ROUTE}/{brick_name}/{unique_name}/register-from-zip"
        )

        try:
            # Create zip file in temporary location
            zip_file_path = tempfile.NamedTemporaryFile(
                suffix=".zip", delete=False
            ).name
            ZipCompress.compress_dir_content(folder_path, zip_file_path)

            # Create form data with the zip file
            form_data = FormData()
            form_data.add_file_from_path("file", zip_file_path, "compose.zip")
            form_data.add_json_data(
                "body",
                options.to_json_dict(),
            )

            ExternalApiService.post_form_data(
                lab_api_url,
                form_data=form_data,
                headers=self._get_request_header(),
                raise_exception_if_error=True,
            )

            # Clean up temporary file
            os.unlink(zip_file_path)

        except BaseHTTPException as err:
            err.detail = f"Can't register compose from zip. Error: {err.detail}"
            raise err

    def register_sqldb_compose(
        self,
        brick_name: str,
        unique_name: str,
        database_name: str,
        options: RegisterSQLDBComposeRequestOptionsDTO,
        disable_volume_backup: bool = False,
        all_environments_networks: bool = False,
    ) -> RegisterSQLDBComposeResponseDTO:
        """
        Register and start a SQL database docker compose.
        The username and password for the database will be created as basic credentials.

        :param brick_name: Name of the brick
        :type brick_name: str
        :param unique_name: Unique name for the compose
        :type unique_name: str
        :param database: Database name
        :type database: str
        :param options: Options for the compose registration
        :type options: RegisterComposeOptionsRequestDTO
        :return: Response containing message and output
        :rtype: DockerComposeResponseDTO
        """
        # Get credentials using the internal method
        credentials = self._get_or_create_basic_credentials_model(
            brick_name=brick_name,
            unique_name=unique_name,
        )

        credentials_data = cast(CredentialsDataBasic, credentials.get_data_object())

        # Create the request DTO with credentials from the credential service
        request_dto = RegisterSQLDBComposeRequestDTO(
            username=credentials_data.username,
            password=credentials_data.password,
            database=database_name,
            options=options,
        )

        lab_api_url = self._get_lab_manager_api_url(
            f"{self._DOCKER_ROUTE}/{brick_name}/{unique_name}/register/sqldb"
        )

        try:
            response = ExternalApiService.post(
                lab_api_url,
                request_dto,
                headers=self._get_request_header(),
                raise_exception_if_error=True,
            )

            sql_response = RegisterSQLDBComposeAPIResponseDTO.from_json(response.json())

            # Update credentials with the actual DB host
            if sql_response.dbHost != credentials_data.url:
                credentials = CredentialsService.update_basic_credential(
                    credentials_name=credentials.name,
                    credentials_data=CredentialsDataBasic(
                        username=credentials_data.username,
                        password=credentials_data.password,
                        url=sql_response.dbHost,
                    ),
                )

            credentials_data = cast(CredentialsDataBasic, credentials.get_data_object())

            return RegisterSQLDBComposeResponseDTO(
                composeStatus=sql_response.status,
                credentials=credentials_data,
            )

        except BaseHTTPException as err:
            err.detail = f"Can't register SQL DB compose. Error: {err.detail}"
            raise err

    def unregister_compose(
        self,
        brick_name: str,
        unique_name: str,
    ) -> SubComposeStatusDTO:
        """
        Stop and unregister a docker compose

        :param brick_name: Name of the brick
        :type brick_name: str
        :param unique_name: Unique name for the compose
        :type unique_name: str
        :param env: Environment of the compose registration (only define when you know what you are doing)
        :type env: RegisterComposeEnv | None
        :return: Response containing message and output
        :rtype: SubComposeStatusDTO
        """

        lab_api_url = self._get_lab_manager_api_url(
            f"{self._DOCKER_ROUTE}/{brick_name}/{unique_name}/unregister"
        )

        try:
            response = ExternalApiService.delete(
                lab_api_url,
                headers=self._get_request_header(),
                raise_exception_if_error=True,
            )

            return SubComposeStatusDTO.from_json(response.json())

        except BaseHTTPException as err:
            err.detail = f"Can't stop compose. Error: {err.detail}"
            raise err

    def get_compose_status(
        self,
        brick_name: str,
        unique_name: str,
    ) -> SubComposeStatusDTO:
        """
        Get the status of a docker compose

        :param brick_name: Name of the brick
        :type brick_name: str
        :param unique_name: Unique name for the compose
        :type unique_name: str
        :param env: Environment of the compose registration (only define when you know what you are doing)
        :type env: RegisterComposeEnv | None
        :return: Status information of the compose
        :rtype: SubComposeStatusDTO
        """

        lab_api_url = self._get_lab_manager_api_url(
            f"{self._DOCKER_ROUTE}/{brick_name}/{unique_name}/status"
        )

        try:
            response = ExternalApiService.get(
                lab_api_url,
                headers=self._get_request_header(),
                raise_exception_if_error=True,
            )

            return SubComposeStatusDTO.from_json(response.json())

        except BaseHTTPException as err:
            err.detail = f"Can't get compose status. Error: {err.detail}"
            raise err

    def wait_for_compose_status(
        self,
        brick_name: str,
        unique_name: str,
        interval_seconds: float = 5.0,
        max_attempts: int = 0,
        message_dispatcher: MessageDispatcher | None = None,
    ) -> SubComposeStatusDTO:
        """
        Wait for the compose status to stabilize (not STARTING or STOPPING)

        :param brick_name: Name of the brick
        :type brick_name: str
        :param unique_name: Unique name for the compose
        :type unique_name: str
        :param interval_seconds: Time in seconds between status checks (default: 5.0). 0 means no limit.
        :type interval_seconds: float
        :param max_attempts: Maximum number of attempts to check the status (default: 12)
        :type max_attempts: int
        :return: Final stable status information of the compose
        :rtype: SubComposeStatusDTO
        """
        attempts = 0
        last_running_message: str | None = None
        while attempts < max_attempts or max_attempts == 0:
            status_info = self.get_compose_status(brick_name, unique_name)

            if not status_info.is_in_progress_status():
                if message_dispatcher is not None:
                    text = f"Docker Compose status: {status_info.composeStatus.status.value}."
                    if status_info.composeStatus.info:
                        text += f" Info: {status_info.composeStatus.info}."

                    if status_info.subComposeProcess:
                        text = f"Docker Compose process info: {status_info.subComposeProcess.status} {status_info.subComposeProcess.message}. "
                        duration = status_info.subComposeProcess.get_duration_seconds()
                        if duration is not None:
                            text += f" Start duration: {DateHelper.get_duration_pretty_text(duration)}."
                    message_dispatcher.notify_info_message(text)

                return status_info

            # Dispatch process message if it has changed
            process_message = status_info.get_process_message()
            if process_message is not None and message_dispatcher is not None:
                if process_message != last_running_message:
                    message_dispatcher.notify_info_message(process_message)
                    last_running_message = process_message

            time.sleep(interval_seconds)

            attempts += 1

        raise Exception(
            f"Compose '{brick_name}/{unique_name}' did not stabilize after {attempts * interval_seconds} seconds"
        )

    def get_all_composes(self) -> SubComposeListDTO:
        """
        Get all docker composes

        :return: List of all compose information
        :rtype: SubComposeListDTO
        """

        lab_api_url = self._get_lab_manager_api_url(f"{self._DOCKER_ROUTE}/list")

        try:
            response = ExternalApiService.get(
                lab_api_url,
                headers=self._get_request_header(),
                raise_exception_if_error=True,
            )

            return SubComposeListDTO.from_json(response.json())

        except BaseHTTPException as err:
            err.detail = f"Can't get all composes. Error: {err.detail}"
            raise err

    def _get_or_create_basic_credentials_model(
        self,
        brick_name: str,
        unique_name: str,
        username: str | None = None,
        password: str | None = None,
        url: str | None = None,
    ) -> Credentials:
        """
        Get or create basic credentials using the brick_name_unique_name format as the credential name.

        :param brick_name: Name of the brick
        :type brick_name: str
        :param unique_name: Unique name for the compose
        :type unique_name: str
        :param username: Username for the credential. If not provided, set to 'brick_name_unique_name'
        :type username: str
        :param password: Password for the credential. If not provided, a random 30-character password will be generated
        :type password: Optional[str]
        :param url: Optional URL for the credential
        :type url: Optional[str]
        :return: The existing or newly created BASIC credential
        :rtype: Credentials
        """
        credentials_name = self.get_basic_credentials_name(brick_name, unique_name)

        if username is None:
            username = f"{brick_name}_{unique_name}"

        return CredentialsService.get_or_create_basic_credential(
            name=credentials_name,
            username=username,
            password=password,
            url=url,
            description=f"Basic credentials for Docker compose {brick_name}/{unique_name}",
        )

    def get_or_create_basic_credentials(
        self,
        brick_name: str,
        unique_name: str,
        username: str | None = None,
        password: str | None = None,
        url: str | None = None,
    ) -> CredentialsDataBasic:
        """
        Get or create basic credentials using the brick_name_unique_name format as the credential name.

        :param brick_name: Name of the brick
        :type brick_name: str
        :param unique_name: Unique name for the compose
        :type unique_name: str
        :param username: Username for the credential. If not provided, set to 'brick_name_unique_name'
        :type username: str
        :param password: Password for the credential. If not provided, a random 30-character password will be generated
        :type password: Optional[str]
        :param url: Optional URL for the credential
        :type url: Optional[str]
        :return: The existing or newly created BASIC credential
        :rtype: Credentials
        """

        credentials = self._get_or_create_basic_credentials_model(
            brick_name=brick_name,
            unique_name=unique_name,
            username=username,
            password=password,
            url=url,
        )

        return cast(CredentialsDataBasic, credentials.get_data_object())

    def get_basic_credentials(
        self, brick_name: str, unique_name: str
    ) -> Credentials | None:
        """
        Get basic credentials using the brick_name_unique_name format as the credential name.

        :param brick_name: Name of the brick
        :type brick_name: str
        :param unique_name: Unique name for the compose
        :type unique_name: str
        :return: The existing BASIC credential or None if not found
        :rtype: Optional[Credentials]
        """
        credentials_name = self.get_basic_credentials_name(brick_name, unique_name)

        return CredentialsService.find_by_name(credentials_name)

    def get_basic_credentials_name(self, brick_name: str, unique_name: str) -> str:
        """
        Get the name of the basic credentials using the brick_name_unique_name format.

        :param brick_name: Name of the brick
        :type brick_name: str
        :param unique_name: Unique name for the compose
        :type unique_name: str
        :return: The name of the BASIC credential
        :rtype: str
        """
        return f"docker_{brick_name}_{unique_name}"

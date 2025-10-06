
import os
import tempfile
import time
from typing import Dict, Literal, Optional, cast

from gws_core.core.exception.exceptions.base_http_exception import \
    BaseHTTPException
from gws_core.core.service.external_api_service import (ExternalApiService,
                                                        FormData)
from gws_core.core.utils.compress.zip_compress import ZipCompress
from gws_core.credentials.credentials_service import CredentialsService
from gws_core.credentials.credentials_type import CredentialsDataBasic
from gws_core.docker.docker_dto import (DockerComposeStatusInfoDTO,
                                        RegisterSQLDBComposeAPIResponseDTO,
                                        RegisterSQLDBComposeRequestDTO,
                                        RegisterSQLDBComposeResponseDTO,
                                        StartComposeRequestDTO,
                                        SubComposeListDTO)
from gws_core.docker.lab_manager_service_base import LabManagerServiceBase


class DockerService(LabManagerServiceBase):

    _DOCKER_ROUTE: str = 'docker-compose'

    def register_and_start_compose(
            self, compose: StartComposeRequestDTO, brick_name: str, unique_name: str) -> None:
        """
        Start a docker compose from string content

        :param compose: The docker-compose content object
        :type compose: StartComposeRequestDTO
        :param brick_name: Name of the brick
        :type brick_name: str
        :param unique_name: Unique name for the compose
        :type unique_name: str
        :param options: Options for starting the compose
        :type options: Optional[StartComposeRequestOptionsDTO]
        :return: Response containing message and output
        :rtype: DockerComposeResponseDTO
        """

        lab_api_url = self._get_lab_manager_api_url(
            f'{self._DOCKER_ROUTE}/sub-compose/{brick_name}/{unique_name}/register')

        try:
            ExternalApiService.post(
                lab_api_url,
                compose,
                headers=self._get_request_header(),
                raise_exception_if_error=True
            )

        except BaseHTTPException as err:
            err.detail = f"Can't start compose from string. Error: {err.detail}"
            raise err

    def unregister_compose(self, brick_name: str, unique_name: str) -> DockerComposeStatusInfoDTO:
        """
        Stop and unregister a docker compose

        :param brick_name: Name of the brick
        :type brick_name: str
        :param unique_name: Unique name for the compose
        :type unique_name: str
        :return: Response containing message and output
        :rtype: DockerComposeResponseDTO
        """

        lab_api_url = self._get_lab_manager_api_url(
            f'{self._DOCKER_ROUTE}/sub-compose/{brick_name}/{unique_name}/unregister')

        try:
            response = ExternalApiService.delete(
                lab_api_url,
                headers=self._get_request_header(),
                raise_exception_if_error=True
            )

            return DockerComposeStatusInfoDTO.from_json(response.json())

        except BaseHTTPException as err:
            err.detail = f"Can't stop compose. Error: {err.detail}"
            raise err

    def get_compose_status(self, brick_name: str, unique_name: str) -> DockerComposeStatusInfoDTO:
        """
        Get the status of a docker compose

        :param brick_name: Name of the brick
        :type brick_name: str
        :param unique_name: Unique name for the compose
        :type unique_name: str
        :return: Status information of the compose
        :rtype: DockerComposeStatusInfoDTO
        """

        lab_api_url = self._get_lab_manager_api_url(
            f'{self._DOCKER_ROUTE}/sub-compose/{brick_name}/{unique_name}/status')

        try:
            response = ExternalApiService.get(
                lab_api_url,
                headers=self._get_request_header(),
                raise_exception_if_error=True
            )

            return DockerComposeStatusInfoDTO.from_json(response.json())

        except BaseHTTPException as err:
            err.detail = f"Can't get compose status. Error: {err.detail}"
            raise err

    def wait_for_compose_status(self, brick_name: str, unique_name: str,
                                interval_seconds: float = 5.0,
                                max_attempts: int = 12) -> DockerComposeStatusInfoDTO:
        """
        Wait for the compose status to stabilize (not STARTING or STOPPING)

        :param brick_name: Name of the brick
        :type brick_name: str
        :param unique_name: Unique name for the compose
        :type unique_name: str
        :param interval_seconds: Time in seconds between status checks (default: 5.0)
        :type interval_seconds: float
        :param max_attempts: Maximum number of attempts to check the status (default: 12)
        :type max_attempts: int
        :return: Final stable status information of the compose
        :rtype: DockerComposeStatusInfoDTO
        """
        attempts = 0
        while attempts < max_attempts:
            status_info = self.get_compose_status(brick_name, unique_name)

            if not status_info.is_in_progress_status():
                return status_info

            time.sleep(interval_seconds)

            attempts += 1

        raise Exception(
            f"Compose '{brick_name}/{unique_name}' did not stabilize after {attempts * interval_seconds} seconds")

    def get_all_composes(self) -> SubComposeListDTO:
        """
        Get all docker composes

        :return: List of all compose information
        :rtype: SubComposeListDTO
        """

        lab_api_url = self._get_lab_manager_api_url(f'{self._DOCKER_ROUTE}/sub-compose/list')

        try:
            response = ExternalApiService.get(
                lab_api_url,
                headers=self._get_request_header(),
                raise_exception_if_error=True
            )

            return SubComposeListDTO.from_json(response.json())

        except BaseHTTPException as err:
            err.detail = f"Can't get all composes. Error: {err.detail}"
            raise err

    def register_sqldb_compose(self, brick_name: str, unique_name: str,
                               database_name: str, description: str,
                               env: Dict[str, str] | None = None) -> RegisterSQLDBComposeResponseDTO:
        """
        Register and start a SQL database docker compose.
        The username and password for the database will be created as basic credentials.

        :param brick_name: Name of the brick
        :type brick_name: str
        :param unique_name: Unique name for the compose
        :type unique_name: str
        :param database: Database name
        :type database: str
        :param description: Description for the compose
        :type description: str
        :param env: Environment variables for the compose
        :type env: Dict[str, str]
        :return: Response containing message and output
        :rtype: DockerComposeResponseDTO
        """
        # Get credentials using the internal method
        credentials_data = self.get_or_create_basic_credentials(
            brick_name=brick_name,
            unique_name=unique_name,
        )

        # Create the request DTO with credentials from the credential service
        request_dto = RegisterSQLDBComposeRequestDTO(
            username=credentials_data.username,
            password=credentials_data.password,
            database=database_name,
            description=description,
            env=env
        )

        lab_api_url = self._get_lab_manager_api_url(
            f'{self._DOCKER_ROUTE}/sub-compose/{brick_name}/{unique_name}/register/sqldb')

        try:
            response = ExternalApiService.post(
                lab_api_url,
                request_dto,
                headers=self._get_request_header(),
                raise_exception_if_error=True
            )

            sql_response = RegisterSQLDBComposeAPIResponseDTO.from_json(response.json())


            return RegisterSQLDBComposeResponseDTO(
                composeStatus=sql_response.status,
                credentials=credentials_data,
                db_host=sql_response.dbHost
            )

        except BaseHTTPException as err:
            err.detail = f"Can't register SQL DB compose. Error: {err.detail}"
            raise err

    def register_sub_compose_from_folder(self, brick_name: str, unique_name: str,
                                         folder_path: str, description: str,
                                         env: Dict[str, str] | None = None) -> DockerComposeStatusInfoDTO:
        """
        Register a docker compose from a folder by zipping it and uploading

        :param brick_name: Name of the brick
        :type brick_name: str
        :param unique_name: Unique name for the compose
        :type unique_name: str
        :param folder_path: Path to the folder containing the compose files
        :type folder_path: str
        :param description: Description for the compose
        :type description: str
        :param env: Environment variables for the compose
        :type env: Dict[str, str]
        :return: Status information of the compose
        :rtype: DockerComposeStatusInfoDTO
        """

        lab_api_url = self._get_lab_manager_api_url(
            f'{self._DOCKER_ROUTE}/sub-compose/{brick_name}/{unique_name}/register-from-zip')

        try:
            # Create zip file in temporary location
            zip_file_path = tempfile.NamedTemporaryFile(suffix='.zip', delete=False).name
            ZipCompress.compress_dir_content(folder_path, zip_file_path)

            # Create form data with the zip file
            form_data = FormData()
            form_data.add_file_from_path('file', zip_file_path, 'compose.zip')
            form_data.add_json_data('body', {'description': description, 'env': env})

            response = ExternalApiService.post_form_data(
                lab_api_url,
                form_data=form_data,
                headers=self._get_request_header(),
                raise_exception_if_error=True
            )

            # Clean up temporary file
            os.unlink(zip_file_path)

            return DockerComposeStatusInfoDTO.from_json(response.json())

        except BaseHTTPException as err:
            err.detail = f"Can't register compose from zip. Error: {err.detail}"
            raise err

    def get_or_create_basic_credentials(self, brick_name: str, unique_name: str,
                                        username: Optional[str] = None,
                                        password: Optional[str] = None,
                                        url: Optional[str] = None) -> CredentialsDataBasic:
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
        credentials_name = f"docker_{brick_name}_{unique_name}"

        if username is None:
            username = f"{brick_name}_{unique_name}"

        credentials = CredentialsService.get_or_create_basic_credential(
            name=credentials_name,
            username=username,
            password=password,
            url=url,
            description=f"Basic credentials for Docker compose {brick_name}/{unique_name}"
        )

        return cast(CredentialsDataBasic, credentials.get_data_object())

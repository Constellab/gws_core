
from gws_core.core.exception.exceptions.base_http_exception import \
    BaseHTTPException
from gws_core.core.service.external_api_service import (ExternalApiService,
                                                        FormData)
from gws_core.docker.docker_dto import (DockerComposeResponseDTO,
                                        DockerComposeStatusInfoDTO,
                                        StartComposeRequestDTO,
                                        SubComposeListDTO)
from gws_core.docker.lab_manager_service_base import LabManagerServiceBase


class DockerService(LabManagerServiceBase):

    _DOCKER_ROUTE: str = 'docker'

    def start_compose_from_file(self, file_path: str, brick_name: str, unique_name: str) -> DockerComposeResponseDTO:
        """
        Start a docker compose from file path

        :param file_path: Path to the docker-compose file
        :type file_path: str
        :param brick_name: Name of the brick
        :type brick_name: str
        :param unique_name: Unique name for the compose
        :type unique_name: str
        :return: Response containing message and output
        :rtype: DockerComposeResponseDTO
        """

        lab_api_url = self._get_lab_manager_api_url(
            f'{self._DOCKER_ROUTE}/compose/{brick_name}/{unique_name}/start-from-file')

        try:
            # Create form data with file
            form_data = FormData()
            form_data.add_file_from_path('file', file_path)

            response = ExternalApiService.post_form_data(
                lab_api_url,
                form_data=form_data,
                headers=self._get_request_header(),
                raise_exception_if_error=True
            )

            return DockerComposeResponseDTO.from_json(response.json())

        except BaseHTTPException as err:
            err.detail = f"Can't start compose from file. Error: {err.detail}"
            raise err

    def start_compose_from_string(
            self, compose_content: str, brick_name: str, unique_name: str) -> DockerComposeResponseDTO:
        """
        Start a docker compose from string content

        :param compose_content: The docker-compose content as string
        :type compose_content: str
        :param brick_name: Name of the brick
        :type brick_name: str
        :param unique_name: Unique name for the compose
        :type unique_name: str
        :return: Response containing message and output
        :rtype: DockerComposeResponseDTO
        """

        lab_api_url = self._get_lab_manager_api_url(f'{self._DOCKER_ROUTE}/compose/{brick_name}/{unique_name}/start')

        try:
            body = StartComposeRequestDTO(composeContent=compose_content)
            response = ExternalApiService.post(
                lab_api_url,
                body,
                headers=self._get_request_header(),
                raise_exception_if_error=True
            )

            return DockerComposeResponseDTO.from_json(response.json())

        except BaseHTTPException as err:
            err.detail = f"Can't start compose from string. Error: {err.detail}"
            raise err

    def delete_compose(self, brick_name: str, unique_name: str) -> DockerComposeResponseDTO:
        """
        Stop a docker compose

        :param brick_name: Name of the brick
        :type brick_name: str
        :param unique_name: Unique name for the compose
        :type unique_name: str
        :return: Response containing message and output
        :rtype: DockerComposeResponseDTO
        """

        lab_api_url = self._get_lab_manager_api_url(f'{self._DOCKER_ROUTE}/compose/{brick_name}/{unique_name}/delete')

        try:
            response = ExternalApiService.delete(
                lab_api_url,
                headers=self._get_request_header(),
                raise_exception_if_error=True
            )

            return DockerComposeResponseDTO.from_json(response.json())

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

        lab_api_url = self._get_lab_manager_api_url(f'{self._DOCKER_ROUTE}/compose/{brick_name}/{unique_name}/status')

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

    def get_all_composes(self) -> SubComposeListDTO:
        """
        Get all docker composes

        :return: List of all compose information
        :rtype: SubComposeListDTO
        """

        lab_api_url = self._get_lab_manager_api_url(f'{self._DOCKER_ROUTE}/compose/list')

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

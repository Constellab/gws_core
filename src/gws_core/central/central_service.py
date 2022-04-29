# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
from typing import Dict, List

from gws_core.brick.brick_service import BrickService
from gws_core.central.central_dto import (CentralSendMailDTO, LabStartDTO,
                                          SaveExperimentToCentralDTO, SaveReportToCentralDTO,
                                          SendExperimentFinishMailData)
from gws_core.experiment.experiment import Experiment
from gws_core.impl.file.file_helper import FileHelper
from gws_core.lab.lab_config_model import LabConfig
from requests.models import Response

from ..core.exception.exceptions import BadRequestException
from ..core.service.base_service import BaseService
from ..core.service.external_api_service import ExternalApiService
from ..core.utils.logger import Logger
from ..core.utils.settings import Settings
from ..project.project_dto import CentralProject
from ..user.credentials_dto import CredentialsDTO
from ..user.current_user_service import CurrentUserService
from ..user.user import User


class CentralService(BaseService):

    # external lab route on central
    _external_labs_route: str = 'external-labs'
    _api_key_header_key: str = 'Authorization'
    _api_key_header_prefix: str = 'api-key '
    # Key to set the user in the request
    _user_id_header_key: str = 'User'

    @classmethod
    def check_api_key(cls, api_key: str) -> bool:

        settings: Settings = Settings.retrieve()

        # In local env, we don't check the api key
        if settings.get_lab_environment() == 'LOCAL':
            return True

        if settings.is_dev:
            raise BadRequestException("The central routes are desactivated in dev environment")

        central_api_key = Settings.get_central_api_key()
        return central_api_key == api_key

    @classmethod
    def check_credentials(cls, credentials: CredentialsDTO) -> bool:
        """
        Check the credential of an email/password by calling central
        and return true if ok
        """
        central_api_url: str = cls._get_central_api_url(
            'auth/login')
        response = ExternalApiService.post(central_api_url, credentials.dict())

        return response.status_code == 201

    @classmethod
    def register_lab_start(cls, lab_config: LabConfig) -> bool:
        """
        Call the central api to mark the lab as started
        """
        central_api_url: str = cls._get_central_api_url(f"{cls._external_labs_route}/start")

        body: LabStartDTO = {
            "lab_config": lab_config
        }

        response = ExternalApiService.put(central_api_url, body, cls._get_request_header())

        if response.status_code != 200:
            BrickService.log_brick_error(
                CentralService, f"Can't register lab start on central. Error : {response.text}")
            return False
        return True

    @classmethod
    def get_current_user_projects(cls) -> List[CentralProject]:
        """
        Call the central api to get the list of project for the current user
        """
        user: User = CurrentUserService.get_and_check_current_user()
        central_api_url: str = cls._get_central_api_url(f"{cls._external_labs_route}/user/{user.id}/projects")
        response = ExternalApiService.get(central_api_url, cls._get_request_header())

        if response.status_code != 200:
            Logger.error(f"Can't retrieve projects for the user {user.id}, {user.email}. Error : {response.text}")
            raise BadRequestException("Can't retrieve projects for current user")

        return response.json()

    @classmethod
    def save_experiment(cls, project_id: str, save_experiment_dto: SaveExperimentToCentralDTO) -> None:
        central_api_url: str = cls._get_central_api_url(
            f"{cls._external_labs_route}/project/{project_id}/experiment")
        response = ExternalApiService.put(central_api_url, save_experiment_dto, cls._get_request_header())

        if response.status_code != 200:
            Logger.error(f"Can't save the experiment in central. Error : {response.text}")
            raise BadRequestException("Can't save the experiment in central")

    @classmethod
    def save_report(cls, project_id: str, report: SaveReportToCentralDTO) -> None:
        central_api_url: str = cls._get_central_api_url(
            f"{cls._external_labs_route}/project/{project_id}/report")

        response = ExternalApiService.put(
            central_api_url, body=report,
            headers=cls._get_request_header())

        if response.status_code != 200:
            Logger.error(f"Can't save the report in central. Error : {response.text}")
            raise BadRequestException("Can't save the report in central")

    @classmethod
    def send_experiment_finished_mail(cls, user_id: str, experiment: SendExperimentFinishMailData) -> None:
        data: CentralSendMailDTO = {
            "receiver_ids": [user_id],
            "mail_template": "experiment-finished",
            "data": {
                "experiment": experiment
            }
        }
        cls._send_mail(data)

    @classmethod
    def _send_mail(cls, send_mail_dto: CentralSendMailDTO) -> Response:
        central_api_url: str = cls._get_central_api_url(
            f"{cls._external_labs_route}/send-mail")
        return ExternalApiService.post(central_api_url, send_mail_dto, cls._get_request_header())

    @classmethod
    def _get_central_api_url(cls, route: str) -> str:
        """
        Build an URL to call the central API
        """

        central_api_url = Settings.get_central_api_url()
        if central_api_url is None:
            raise BadRequestException('The CENTRAL_API_URL environment variable is not set')
        return central_api_url + '/' + route

    @classmethod
    def _get_request_header(cls) -> Dict[str, str]:
        """
        Return the header for a request to central, with Api key and User if exists
        """
        # Header with the Api Key
        headers = {cls._api_key_header_key: cls._api_key_header_prefix + Settings.get_central_api_key()}

        user: User = CurrentUserService.get_current_user()

        if user:
            headers[cls._user_id_header_key] = user.id

        return headers

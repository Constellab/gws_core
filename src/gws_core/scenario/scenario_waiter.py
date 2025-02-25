

import time
from abc import abstractmethod
from typing import Optional

from numpy import Infinity

from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.credentials.credentials_type import CredentialsDataLab
from gws_core.external_lab.external_lab_api_service import \
    ExternalLabApiService
from gws_core.external_lab.external_lab_dto import \
    ExternalLabImportScenarioResponseDTO
from gws_core.scenario.scenario import Scenario
from gws_core.scenario.scenario_dto import ScenarioDTO, ScenarioProgressDTO
from gws_core.scenario.scenario_enums import ScenarioStatus


class ScenarioWaitInfoDTO(BaseModelDTO):
    scenario: ScenarioDTO
    progress: Optional[ScenarioProgressDTO] = None


class ScenarioWaiter():

    # Number of consecutive get error before raising an exception
    CONSECUTIVE_GET_ERROR_THRESHOLD = 2

    @abstractmethod
    def get_scenario_dto(self) -> ScenarioWaitInfoDTO:
        pass

    def wait_until_finished(self, refresh_interval: int = 30,
                            refresh_interval_max_count: int = 10,
                            message_dispatcher: MessageDispatcher = None) -> ScenarioWaitInfoDTO:
        """ Wait until the scenario is finished.
        If the scenario is in draft mode, it will raise an exception

        :param refresh_interval: interval in seconds between each refresh, defaults to 30
        :type refresh_interval: int, optional
        :param refresh_interval_max_count: maximum number of refresh, if reached, it will raise an exception
                                            set -1 to wait indefinitely, defaults to 10
        :type refresh_interval_max_count: int, optional
        :param message_dispatcher: message dispatcher to send messages. If provided, the progress
                                of scenario is emitted in message_dispatcher, defaults to None
        :type message_dispatcher: MessageDispatcher, optional
        :return: the scenario
        :rtype: ScenarioDTO
        """

        count = 0
        consecutive_get_error = 0

        max_refresh = refresh_interval_max_count if refresh_interval_max_count > 0 else Infinity
        while count < max_refresh:
            count += 1

            scenario: ScenarioWaitInfoDTO = None
            try:
                scenario = self.get_scenario_dto()
            except Exception as e:
                consecutive_get_error += 1
                if consecutive_get_error >= self.CONSECUTIVE_GET_ERROR_THRESHOLD:
                    raise e
                if message_dispatcher:
                    message_dispatcher.notify_error_message(f"Error while getting scenario. Error : {str(e)}")
                continue

            consecutive_get_error = 0

            if scenario.scenario.status == ScenarioStatus.DRAFT:
                raise Exception("Scenario is in draft mode")
            if scenario.scenario.status in [ScenarioStatus.SUCCESS, ScenarioStatus.ERROR, ScenarioStatus.PARTIALLY_RUN]:
                return scenario

            if message_dispatcher and scenario.progress:
                message = scenario.progress.get_last_message_content() or "Update progress"
                message_dispatcher.notify_progress_value(
                    scenario.progress.progress, message)
            time.sleep(refresh_interval)

        raise Exception("Scenario is taking too long to finish, max refresh reached")


class ScenarioWaiterBasic(ScenarioWaiter):

    scenario_id: str

    def __init__(self, scenario_id: str):
        """ Waiter to check a scenario

        :param scenario_id: scenario id
        :type scenario_id: str
        """
        super().__init__()
        self.scenario_id = scenario_id

    def get_scenario_dto(self) -> ScenarioWaitInfoDTO:
        scenario = self.get_scenario()

        return ScenarioWaitInfoDTO(scenario=scenario.to_dto(), progress=scenario.get_current_progress())

    def get_scenario(self) -> Scenario:
        return Scenario.get_by_id_and_check(self.scenario_id)


class ScenarioWaiterExternalLab(ScenarioWaiter):

    scenario_id: str
    lab_credentials: CredentialsDataLab
    user_id: str

    def __init__(self, scenario_id: str, lab_credentials: CredentialsDataLab, user_id: str):
        """ Waiter to check a scenario of an external lab

        :param scenario_id: scenario id
        :type scenario_id: str
        :param lab_credentials: credentials to access the lab
        :type lab_credentials: CredentialsDataLab
        :param user_id: current user id
        :type user_id: str
        """
        super().__init__()
        self.scenario_id = scenario_id
        self.lab_credentials = lab_credentials
        self.user_id = user_id

    def get_scenario_dto(self) -> ScenarioWaitInfoDTO:
        scenario_import = self.get_scenario_import_info()

        return ScenarioWaitInfoDTO(scenario=scenario_import.scenario,
                                   progress=scenario_import.scenario_progress)

    def get_scenario_import_info(self) -> ExternalLabImportScenarioResponseDTO:
        return ExternalLabApiService.get_scenario(self.scenario_id, self.lab_credentials, self.user_id)

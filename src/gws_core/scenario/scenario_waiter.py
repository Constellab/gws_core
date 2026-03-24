import time
from abc import abstractmethod

from numpy import Infinity

from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.external_lab.external_lab_api_service import ExternalLabApiService
from gws_core.external_lab.external_lab_dto import ExternalLabImportScenarioResponseDTO
from gws_core.scenario.scenario import Scenario
from gws_core.scenario.scenario_dto import ScenarioDTO, ScenarioProgressDTO
from gws_core.scenario.scenario_enums import ScenarioStatus


class ScenarioWaitInfoDTO(BaseModelDTO):
    scenario: ScenarioDTO
    progress: ScenarioProgressDTO | None = None


class ScenarioWaiter:
    # Number of consecutive get error before raising an exception
    CONSECUTIVE_GET_ERROR_THRESHOLD = 2

    _message_dispatcher: MessageDispatcher | None

    def __init__(self, message_dispatcher: MessageDispatcher | None = None):
        """
        :param message_dispatcher: message dispatcher to send messages, defaults to None
        :type message_dispatcher: MessageDispatcher, optional
        """
        self._message_dispatcher = message_dispatcher

    @abstractmethod
    def get_scenario_dto(self) -> ScenarioWaitInfoDTO:
        pass

    def wait_until_finished(
        self,
        refresh_interval: int = 30,
        refresh_interval_max_count: int = 10,
        raise_on_excluded: bool = True,
    ) -> ScenarioWaitInfoDTO:
        """Wait until the scenario is finished.
        If the scenario is in draft mode, it will raise an exception (unless raise_on_excluded is False).

        :param refresh_interval: interval in seconds between each refresh, defaults to 30
        :type refresh_interval: int, optional
        :param refresh_interval_max_count: maximum number of refresh, if reached, it will raise an exception
                                            set -1 to wait indefinitely, defaults to 10
        :type refresh_interval_max_count: int, optional
        :param raise_on_excluded: if True, raise an exception when an excluded status is reached.
                                   If False, return the scenario instead, defaults to True
        :type raise_on_excluded: bool, optional
        :return: the scenario
        :rtype: ScenarioWaitInfoDTO
        """
        return self.wait_until_status(
            target_statuses=[
                ScenarioStatus.SUCCESS,
                ScenarioStatus.ERROR,
                ScenarioStatus.PARTIALLY_RUN,
            ],
            excluded_statuses=[ScenarioStatus.DRAFT],
            raise_on_excluded=raise_on_excluded,
            refresh_interval=refresh_interval,
            refresh_interval_max_count=refresh_interval_max_count,
        )

    def wait_for_scenario_to_start(
        self,
        refresh_interval: int = 30,
        refresh_interval_max_count: int = 10,
        raise_on_excluded: bool = True,
    ) -> ScenarioWaitInfoDTO:
        """Wait until the scenario is running.
        This should be called when the scenario is in the queue or running async.
        If the scenario reaches an excluded status (draft or already finished),
        it will raise an exception (unless raise_on_excluded is False).

        :param refresh_interval: interval in seconds between each refresh, defaults to 30
        :type refresh_interval: int, optional
        :param refresh_interval_max_count: maximum number of refresh, if reached, it will raise an exception
                                            set -1 to wait indefinitely, defaults to 10
        :type refresh_interval_max_count: int, optional
        :param raise_on_excluded: if True, raise an exception when an excluded status is reached.
                                   If False, return the scenario instead, defaults to True
        :type raise_on_excluded: bool, optional
        :return: the scenario
        :rtype: ScenarioWaitInfoDTO
        """

        return self.wait_until_status(
            target_statuses=[ScenarioStatus.RUNNING],
            excluded_statuses=[
                ScenarioStatus.DRAFT,
                ScenarioStatus.SUCCESS,
                ScenarioStatus.ERROR,
                ScenarioStatus.PARTIALLY_RUN,
            ],
            raise_on_excluded=raise_on_excluded,
            refresh_interval=refresh_interval,
            refresh_interval_max_count=refresh_interval_max_count,
        )

    def wait_until_status(
        self,
        target_statuses: list[ScenarioStatus],
        excluded_statuses: list[ScenarioStatus] | None = None,
        raise_on_excluded: bool = True,
        refresh_interval: int = 30,
        refresh_interval_max_count: int = 10,
    ) -> ScenarioWaitInfoDTO:
        """Wait until the scenario reaches one of the target statuses.
        If the scenario reaches an excluded status, it will either raise an exception
        or return the scenario depending on raise_on_excluded.

        :param target_statuses: list of statuses to wait for
        :type target_statuses: list[ScenarioStatus]
        :param excluded_statuses: list of statuses that should stop the wait if reached, defaults to None
        :type excluded_statuses: list[ScenarioStatus] | None, optional
        :param raise_on_excluded: if True, raise an exception when an excluded status is reached.
                                   If False, return the scenario instead, defaults to True
        :type raise_on_excluded: bool, optional
        :param refresh_interval: interval in seconds between each refresh, defaults to 30
        :type refresh_interval: int, optional
        :param refresh_interval_max_count: maximum number of refresh, if reached, it will raise an exception
                                            set -1 to wait indefinitely, defaults to 10
        :type refresh_interval_max_count: int, optional
        :return: the scenario
        :rtype: ScenarioWaitInfoDTO
        """

        count = 0
        consecutive_get_error = 0

        max_refresh = refresh_interval_max_count if refresh_interval_max_count > 0 else Infinity
        while count < max_refresh:
            count += 1

            scenario: ScenarioWaitInfoDTO | None = None
            try:
                scenario = self.get_scenario_dto()
            except Exception as e:
                consecutive_get_error += 1
                if consecutive_get_error >= self.CONSECUTIVE_GET_ERROR_THRESHOLD:
                    raise e
                if self._message_dispatcher:
                    self._message_dispatcher.notify_error_message(
                        f"Error while getting scenario. Error : {str(e)}"
                    )
                continue

            consecutive_get_error = 0

            if scenario.scenario.status in target_statuses:
                return scenario

            if excluded_statuses and scenario.scenario.status in excluded_statuses:
                if raise_on_excluded:
                    raise Exception(
                        f"Scenario reached an unexpected status: {scenario.scenario.status.value}"
                    )
                return scenario

            if self._message_dispatcher and scenario.progress:
                message = scenario.progress.get_last_message_content() or "Update progress"
                self._message_dispatcher.notify_progress_value(scenario.progress.progress, message)
            time.sleep(refresh_interval)

        raise Exception(
            "Scenario is taking too long to reach the expected status, max refresh reached"
        )


class ScenarioWaiterBasic(ScenarioWaiter):
    scenario_id: str

    def __init__(self, scenario_id: str, message_dispatcher: MessageDispatcher | None = None):
        """Waiter to check a scenario

        :param scenario_id: scenario id
        :type scenario_id: str
        :param message_dispatcher: message dispatcher to send messages, defaults to None
        :type message_dispatcher: MessageDispatcher, optional
        """
        super().__init__(message_dispatcher)
        self.scenario_id = scenario_id

    def get_scenario_dto(self) -> ScenarioWaitInfoDTO:
        scenario = self.get_scenario()

        return ScenarioWaitInfoDTO(
            scenario=scenario.to_dto(), progress=scenario.get_current_progress()
        )

    def get_scenario(self) -> Scenario:
        return Scenario.get_by_id_and_check(self.scenario_id)


class ScenarioWaiterExternalLab(ScenarioWaiter):
    scenario_id: str
    _external_lab_service: ExternalLabApiService

    def __init__(
        self,
        external_lab_service: ExternalLabApiService,
        scenario_id: str,
        message_dispatcher: MessageDispatcher | None = None,
    ):
        """Waiter to check a scenario of an external lab

        :param external_lab_service: external lab API service instance
        :type external_lab_service: ExternalLabApiService
        :param scenario_id: scenario id
        :type scenario_id: str
        :param message_dispatcher: message dispatcher to send messages, defaults to None
        :type message_dispatcher: MessageDispatcher, optional
        """
        super().__init__(message_dispatcher)
        self._external_lab_service = external_lab_service
        self.scenario_id = scenario_id

    def get_scenario_dto(self) -> ScenarioWaitInfoDTO:
        scenario_import = self.get_scenario_import_info()

        return ScenarioWaitInfoDTO(
            scenario=scenario_import.scenario, progress=scenario_import.scenario_progress
        )

    def get_scenario_import_info(self) -> ExternalLabImportScenarioResponseDTO:
        return self._external_lab_service.get_scenario(self.scenario_id)

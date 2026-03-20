from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.external_lab.external_lab_api_service import ExternalLabApiService
from gws_core.scenario.scenario import Scenario
from gws_core.scenario.scenario_waiter import ScenarioWaiter, ScenarioWaitInfoDTO
from gws_core.scenario.task.scenario_downloader_from_lab import ScenarioDownloaderFromLab
from gws_core.task.task_runner import TaskRunner


class ScenarioWaiterExternalLabWithSync(ScenarioWaiter):
    """Waiter for a scenario running in an external lab that downloads
    the scenario structure on each poll using ``ScenarioDownloaderFromLab``.

    Each call to ``get_scenario_dto`` runs the downloader via ``TaskRunner``
    with resource_mode=None, skip_scenario_tags=True, skip_resource_tags=True
    and create_option="Update if exists", then returns the scenario status
    from the downloaded local scenario.
    """

    scenario_id: str
    _external_lab_service: ExternalLabApiService
    _lab_model_id: str

    def __init__(
        self,
        external_lab_service: ExternalLabApiService,
        scenario_id: str,
        lab_model_id: str,
        message_dispatcher: MessageDispatcher | None = None,
    ):
        """
        :param external_lab_service: external lab API service instance
        :type external_lab_service: ExternalLabApiService
        :param scenario_id: scenario id in the external lab
        :type scenario_id: str
        :param lab_model_id: id of the lab model to use for downloading
        :type lab_model_id: str
        :param message_dispatcher: message dispatcher to send messages, defaults to None
        :type message_dispatcher: MessageDispatcher, optional
        """
        super().__init__(message_dispatcher)
        self._external_lab_service = external_lab_service
        self.scenario_id = scenario_id
        self._lab_model_id = lab_model_id

    def get_scenario_dto(self) -> ScenarioWaitInfoDTO:
        """Download the scenario from the external lab and return its status.

        Runs ``ScenarioDownloaderFromLab`` via ``TaskRunner`` with no resources,
        skipping all tags, and using "Update if exists" create option.
        """
        params = ScenarioDownloaderFromLab.build_config(
            lab=self._lab_model_id,
            scenario_id=self.scenario_id,
            resource_mode="None",
            create_option="Update if exists",
            auto_run=False,
            skip_scenario_tags=True,
            skip_resource_tags=True,
        )

        task_runner = TaskRunner(
            task_type=ScenarioDownloaderFromLab,
            params=params,
            message_dispatcher=self._message_dispatcher,
        )

        task_runner.run()

        scenario = Scenario.get_by_id_and_check(self.scenario_id)

        return ScenarioWaitInfoDTO(
            scenario=scenario.to_dto(),
            progress=scenario.get_current_progress(),
        )

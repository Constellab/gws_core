from inspect import isclass
from time import sleep

from gws_core.core.db.process_db import ProcessDb
from gws_core.core.service.front_service import FrontService
from gws_core.entity_navigator.entity_navigator_service import EntityNavigatorService
from gws_core.external_lab.external_lab_api_service import ExternalLabApiService
from gws_core.scenario.queue.queue_service import QueueService
from gws_core.scenario.scenario_exception import ScenarioRunException
from gws_core.scenario.scenario_waiter import ScenarioWaiterBasic
from gws_core.tag.tag import Tag
from gws_core.tag.tag_entity_type import TagEntityType
from gws_core.tag.tag_service import TagService
from gws_core.tag.tag_system import TagSystem
from gws_core.user.current_user_service import CurrentUserService

from ..folder.space_folder import SpaceFolder
from ..protocol.protocol import Protocol
from ..protocol.protocol_proxy import ProtocolProxy
from .scenario import Scenario
from .scenario_enums import ScenarioCreationType, ScenarioStatus
from .scenario_run_service import ScenarioRunService
from .scenario_search_builder import ScenarioSearchBuilder
from .scenario_service import ScenarioService


class ScenarioProxy:
    """Object to simplify scenario creation, configuration and run.
    This can be used in a Jupyter Notebook

    :raises Exception: [description]
    :return: [description]
    :rtype: [type]
    """

    _scenario: Scenario
    _protocol: ProtocolProxy

    START_SCENARIO_TIMEOUT = 30  # seconds

    def __init__(
        self,
        protocol_type: type[Protocol] | None = None,
        folder: SpaceFolder | None = None,
        title: str = "",
        creation_type: ScenarioCreationType = ScenarioCreationType.AUTO,
        scenario_id: str | None = None,
    ) -> None:
        """This create a scenario in the database with the provided Task or Protocol

        :param process_type: Can be the type of a Protocol or a Task.
                            If this is a task, it will be wrapped in a protocol
                            If none it will create an empty protocol in the scenario
        :type process_type: Type[Process]
        :param folder: scenario title, defaults to ''
        :type folder: str, optional
        :param title: scenario title, defaults to ''
        :type title: str, optional
        :param creation_type: type of the created scenario, defaults to ScenarioExecutionType.AUTO
        :type creation_type: ScenarioExecutionType, optional
        :param scenario_id: If provided, other parameters are ignored, it loads an existing scenario, defaults to None
        :type scenario_id: str, optional
        :raises Exception: [description]
        """

        if scenario_id is not None:
            self._scenario = ScenarioService.get_by_id_and_check(scenario_id)
            self._protocol = ProtocolProxy(self._scenario.protocol_model)
            return

        if protocol_type is None:
            self._scenario = ScenarioService.create_scenario(
                title=title, folder_id=folder, creation_type=creation_type
            )
        else:
            if not isclass(protocol_type) or not issubclass(protocol_type, Protocol):
                raise Exception(
                    f"The provided process_type '{str(protocol_type)}' is not a process"
                )
            self._scenario = ScenarioService.create_scenario_from_protocol_type(
                protocol_type=protocol_type, title=title, folder=folder, creation_type=creation_type
            )

        # Init the IProtocol
        self._protocol = ProtocolProxy(self._scenario.protocol_model)

    @staticmethod
    def from_existing_scenario(scenario_id: str) -> "ScenarioProxy":
        """Create a ScenarioProxy from an existing scenario

        :param scenario_id: id of the scenario
        :type scenario_id: str
        :return: [description]
        :rtype: ScenarioProxy
        """
        return ScenarioProxy(scenario_id=scenario_id)

    def get_protocol(self) -> ProtocolProxy:
        """retrieve the main protocol of the scenario"""
        return self._protocol

    def run(self, auto_delete_if_error: bool = False) -> None:
        """execute the scenario, after that the resource should be generated and can be retrieve by process"""

        # run the scenario in a sub process so it can be stopped
        process = ProcessDb(target=ScenarioRunService.run_scenario_by_id, args=(self._scenario.id,))
        process.start()
        process.join()  # Wait for process to complete

        exitcode = process.exitcode

        self.refresh()

        if self._scenario.is_error:
            if auto_delete_if_error:
                self.delete()
            error_info = self._scenario.get_error_info()
            if error_info:
                raise ScenarioRunException(self._scenario, error_info.detail)
            else:
                raise ScenarioRunException(
                    self._scenario, "Error during the execution of the scenario"
                )

        if exitcode != 0:
            raise ScenarioRunException(
                self._scenario, "Error in during the execution of the scenario"
            )

    def run_async(self) -> ScenarioWaiterBasic:
        """Run the scenario in a separate CLI process but don't wait for it to finish.

        Uses a CLI subprocess (like the queue runner) instead of fork to avoid
        inheriting the parent's server socket and event loop state, which can
        block other HTTP requests.

        :return: the scenario waiter
        :rtype: ScenarioWaiterBasic
        """
        user = CurrentUserService.get_and_check_current_user()
        ScenarioRunService.create_cli_for_scenario(self._scenario, user)

        # Wait for scenario to start running
        count = 0
        while count < self.START_SCENARIO_TIMEOUT / 2:
            self.refresh()
            if not self._scenario.is_draft:
                break

            count += 1
            sleep(2)

        if self._scenario.is_draft:
            raise Exception("The scenario is still in draft mode, it was not started")

        return ScenarioWaiterBasic(self._scenario.id)

    def add_to_queue(self) -> None:
        QueueService.add_scenario_to_queue(self._scenario.id)

    def stop_or_remove_from_queue(self) -> "ScenarioProxy":
        """Stop the scenario or remove it from the queue depending on its current status.

        - If the scenario is running in an external lab, stop all running importing scenarios.
        - If the scenario is running locally, stop it.
        - If the scenario is in queue, remove it from the queue.

        :return: the updated scenario
        :rtype: ScenarioProxy
        """
        self.refresh()

        if self._scenario.is_running_in_external_lab:
            self._stop_running_in_external_lab()
        elif self._scenario.is_running:
            ScenarioRunService.stop_scenario(self._scenario.id)
        elif self._scenario.status == ScenarioStatus.IN_QUEUE:
            QueueService.remove_scenario_from_queue(self._scenario.id)
        else:
            raise Exception("The scenario is not running or in queue, it cannot be stopped")

        return self.refresh()

    def _stop_running_in_external_lab(self) -> None:
        """Stop the scenario if it's running in an external lab.

        If the external lab reference is not available or if an error occurs
        while communicating with the external lab, unmark the scenario as running
        and stop all running importing scenarios.
        """
        if self._scenario.running_in_external_lab is None:
            self._stop_all_running_importing_scenarios()
            ScenarioRunService.stop_scenario(self._scenario.id)
            return

        try:
            ExternalLabApiService(
                self._scenario.running_in_external_lab.to_dto_with_credentials()
            ).stop_scenario(self._scenario.id)
            # Refresh the scenario to update its status after stopping it in the external lab
        except Exception:
            self._stop_all_running_importing_scenarios()
            ScenarioRunService.stop_scenario(self._scenario.id)

    def _stop_all_running_importing_scenarios(self) -> None:
        """Stop all currently running scenarios that are importing the current scenario."""
        search_builder = ScenarioSearchBuilder()
        search_builder.add_tag_filter(Tag(TagSystem.SCENARIO_IMPORTER_TAG_KEY, self.get_model_id()))
        search_builder.add_running_filter()

        running_scenarios: list[Scenario] = search_builder.search_all()

        for scenario in running_scenarios:
            ScenarioRunService.stop_scenario(scenario.id)

    def stop(self) -> None:
        ScenarioRunService.stop_scenario(self._scenario.id)

    def delete(self) -> None:
        EntityNavigatorService.delete_scenario(self._scenario.id)

    def get_model(self) -> Scenario:
        return self._scenario

    def get_model_id(self) -> str:
        return self._scenario.id

    def is_running(self) -> bool:
        return self._scenario.is_running

    def is_finished(self) -> bool:
        return self._scenario.is_finished

    def is_success(self) -> bool:
        return self._scenario.is_success

    def add_tag(self, tag: Tag) -> None:
        TagService.add_tag_to_entity(TagEntityType.SCENARIO, self._scenario.id, tag)

    def add_tags(self, tags: list[Tag]) -> None:
        TagService.add_tags_to_entity(TagEntityType.SCENARIO, self._scenario.id, tags)

    def refresh(self) -> "ScenarioProxy":
        self._scenario = self._scenario.refresh()
        self._protocol.refresh()

        return self

    def reset(self) -> "ScenarioProxy":
        """Reset the scenario to draft and delete all logs and progress"""
        EntityNavigatorService.reset_scenario(self._scenario.id)
        self.refresh()
        return self

    def reset_error_processes(self) -> "ScenarioProxy":
        """Reset all processes in error of the scenario"""
        EntityNavigatorService.reset_error_processes_of_protocol(self._scenario.protocol_model)
        self.refresh()
        return self

    def get_url(self) -> str:
        return FrontService().get_scenario_url(self._scenario.id)

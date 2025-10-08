

from inspect import isclass
from time import sleep
from typing import List, Type

from gws_core.core.db.process_db import ProcessDb
from gws_core.core.service.front_service import FrontService
from gws_core.entity_navigator.entity_navigator_service import EntityNavigatorService
from gws_core.scenario.scenario_waiter import ScenarioWaiterBasic
from gws_core.tag.tag import Tag
from gws_core.tag.tag_entity_type import TagEntityType
from gws_core.tag.tag_service import TagService

from ..folder.space_folder import SpaceFolder
from ..protocol.protocol import Protocol
from ..protocol.protocol_proxy import ProtocolProxy
from .scenario import Scenario
from .scenario_enums import ScenarioCreationType
from .scenario_run_service import ScenarioRunService
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

    def __init__(
            self,
            protocol_type: Type[Protocol] = None,
            folder: SpaceFolder = None,
            title: str = '',
            creation_type: ScenarioCreationType = ScenarioCreationType.AUTO,
            scenario_id: str = None) -> None:
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
                title=title, folder_id=folder, creation_type=creation_type)
        else:
            if not isclass(protocol_type) or not issubclass(protocol_type, Protocol):
                raise Exception(
                    f"The provided process_type '{str(protocol_type)}' is not a process")
            self._scenario = ScenarioService.create_scenario_from_protocol_type(
                protocol_type=protocol_type, title=title, folder=folder, creation_type=creation_type)

        # Init the IProtocol
        self._protocol = ProtocolProxy(self._scenario.protocol_model)

    @staticmethod
    def from_existing_scenario(scenario_id: str) -> 'ScenarioProxy':
        """Create a ScenarioProxy from an existing scenario

        :param scenario_id: id of the scenario
        :type scenario_id: str
        :return: [description]
        :rtype: ScenarioProxy
        """
        return ScenarioProxy(scenario_id=scenario_id)

    def get_protocol(self) -> ProtocolProxy:
        """retrieve the main protocol of the scenario
        """
        return self._protocol

    def run(self, auto_delete_if_error: bool = False) -> None:
        """execute the scenario, after that the resource should be generated and can be retrieve by process
        """

        # run the scenario in a sub process so it can be stopped
        process = ProcessDb(
            target=ScenarioRunService.run_scenario_by_id,
            args=(self._scenario.id,)
        )
        process.start()
        process.join()  # Wait for process to complete

        exitcode = process.exitcode

        self.refresh()

        if self._scenario.is_error:
            if auto_delete_if_error:
                self.delete()
            raise Exception(self._scenario.get_error_info().detail)

        if exitcode != 0:
            raise Exception("Error in during the execution of the scenario")

    def run_async(self) -> ScenarioWaiterBasic:
        """Run the scenario in a separate process but don't wait for it to finish

        :return: the scenario waiter
        :rtype: ScenarioWaiterBasic
        """
        # Pass only the scenario ID to avoid Peewee connection issues across processes
        scenario_id = self._scenario.id

        # Create and start a background process with clean db connection
        process = ProcessDb(
            target=ScenarioRunService.run_scenario_by_id,
            args=(scenario_id,)
        )
        process.start()

        # Wait for scenario to start running
        count = 0
        while count < 15:
            self.refresh()
            if not self._scenario.is_draft:
                break

            count += 1
            sleep(2)

        if self._scenario.is_draft:
            raise Exception("The scenario is still in draft mode, it was not started")

        return ScenarioWaiterBasic(self._scenario.id)

    def add_to_queue(self) -> None:
        from gws_core.scenario.queue_service import QueueService

        QueueService.add_scenario_to_queue(self._scenario.id)

    def stop(self) -> None:
        ScenarioRunService.stop_scenario(self._scenario.id)

    def delete(self) -> None:
        ScenarioService.delete_scenario(self._scenario.id)

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
        TagService.add_tag_to_entity(TagEntityType.SCENARIO, self._scenario.id,
                                     tag)

    def add_tags(self, tags: List[Tag]) -> None:
        TagService.add_tags_to_entity(TagEntityType.SCENARIO, self._scenario.id,
                                      tags)

    def refresh(self) -> 'ScenarioProxy':
        self._scenario = self._scenario.refresh()
        self._protocol.refresh()

        return self

    def reset(self) -> 'ScenarioProxy':
        """Reset the scenario to draft and delete all logs and progress
        """
        EntityNavigatorService.reset_scenario(self._scenario.id)
        self.refresh()
        return self

    def get_url(self) -> str:
        return FrontService.get_scenario_url(self._scenario.id)

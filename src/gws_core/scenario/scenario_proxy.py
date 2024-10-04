

from inspect import isclass
from multiprocessing import Process
from time import sleep
from typing import List, Type

from gws_core.entity_navigator.entity_navigator_type import EntityType
from gws_core.tag.tag import Tag
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
            self, protocol_type: Type[Protocol] = None, folder: SpaceFolder = None, title: str = '',
            creation_type: ScenarioCreationType = ScenarioCreationType.AUTO):
        """This create an scenario in the database with the provided Task or Protocol

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
        :raises Exception: [description]
        """

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

    def get_protocol(self) -> ProtocolProxy:
        """retrieve the main protocol of the scenario
        """
        return self._protocol

    def run(self, auto_delete_if_error: bool = False) -> None:
        """execute the scenario, after that the resource should be generated and can be retrieve by process
        """

        # run the scenario in a sub process so it can be stopped
        process = Process(
            target=ScenarioRunService.run_scenario, args=(self._scenario,))
        process.start()
        process.join()

        self.refresh()

        if self._scenario.is_error:
            if auto_delete_if_error:
                self.delete()
            raise Exception(self._scenario.get_error_info().detail)

        # when stop manually the scenario, wait a bit for the status to be updated
        # because the scenario status is updated after the process is stopped
        if process.exitcode is None:
            sleep(2)
            self.refresh()
            if self._scenario.is_error:
                raise Exception(self._scenario.get_error_info().detail)

        if process.exitcode != 0:
            raise Exception("Error in during the execution of the scenario")

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
        TagService.add_tag_to_entity(EntityType.SCENARIO, self._scenario.id,
                                     tag)

    def add_tags(self, tags: List[Tag]) -> None:
        TagService.add_tags_to_entity(EntityType.SCENARIO, self._scenario.id,
                                      tags)

    def refresh(self) -> 'ScenarioProxy':
        self._scenario = self._scenario.refresh()
        self._protocol.refresh()

        return self



from typing import Optional

from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.folder.space_folder import SpaceFolder
from gws_core.protocol.protocol_dto import ScenarioProtocolDTO
from gws_core.protocol.protocol_graph_factory import ProtocolGraphFactory
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.scenario.scenario import Scenario
from gws_core.scenario.scenario_enums import ScenarioCreationType
from gws_core.scenario.scenario_zipper import ZipScenario, ZipScenarioInfo


class ScenarioLoader():

    exp_info: ZipScenarioInfo

    _scenario: Scenario
    _protocol_model: ProtocolModel

    _message_dispatcher: MessageDispatcher

    def __init__(self, scenario_info: ZipScenarioInfo,
                 message_dispatcher: Optional[MessageDispatcher] = None) -> None:
        self.exp_info = scenario_info

        if message_dispatcher is None:
            self._message_dispatcher = MessageDispatcher()
        else:
            self._message_dispatcher = message_dispatcher

    def load_scenario(self) -> Scenario:

        self._scenario = self._load_scenario(self.exp_info.scenario)

        # load the protocol
        protocol_model = self._load_protocol_model(self.exp_info.protocol)
        protocol_model.set_scenario(self._scenario)
        self._protocol_model = protocol_model

        return self._scenario

    def _load_scenario(self, zip_scenario: ZipScenario) -> Scenario:
        # create the scenario and load the info
        scenario = Scenario()
        scenario.title = zip_scenario.title
        scenario.creation_type = ScenarioCreationType.IMPORTED
        scenario.description = zip_scenario.description
        scenario.status = zip_scenario.status

        if zip_scenario.folder is not None:
            folder = SpaceFolder.get_by_id(zip_scenario.folder.id)

            if folder is None:
                self._message_dispatcher.notify_info_message(
                    f"Folder '{zip_scenario.folder.title}' not found, skipping linking scenario to folder.")
            else:
                scenario.folder = folder

        if zip_scenario.error_info is not None:
            scenario.set_error_info(zip_scenario.error_info)

        return scenario

    def _load_protocol_model(self, protocol: ScenarioProtocolDTO) -> ProtocolModel:
        return ProtocolGraphFactory.create_protocol_model_from_config(protocol.data)

    def get_scenario(self) -> Scenario:
        if self._scenario is None:
            raise Exception("Scenario not loaded, call load_scenario first")
        return self._scenario

    def get_protocol_model(self) -> ProtocolModel:
        if self._protocol_model is None:
            raise Exception("Protocol model not loaded, call load_scenario first")

        return self._protocol_model

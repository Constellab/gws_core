

from typing import List, Optional

from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.folder.space_folder import SpaceFolder
from gws_core.protocol.protocol_dto import ScenarioProtocolDTO
from gws_core.protocol.protocol_graph_factory import \
    ProtocolGraphFactoryFromConfig
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.scenario.scenario import Scenario
from gws_core.scenario.scenario_enums import ScenarioCreationType
from gws_core.scenario.scenario_zipper import ZipScenario, ZipScenarioInfo
from gws_core.share.shared_dto import ShareEntityCreateMode
from gws_core.tag.tag import Tag
from gws_core.tag.tag_helper import TagHelper


# TODO doesn't work if a task uses a resource typing (input or output) not
# available in the lab. Or if we download a resource that uses a typing not
# available in the lab.
class ScenarioLoader():

    exp_info: ZipScenarioInfo

    _scenario: Scenario
    _protocol_model: ProtocolModel

    _message_dispatcher: MessageDispatcher

    _mode: ShareEntityCreateMode

    def __init__(self, scenario_info: ZipScenarioInfo,
                 mode: ShareEntityCreateMode,
                 message_dispatcher: Optional[MessageDispatcher] = None) -> None:
        self.exp_info = scenario_info

        if message_dispatcher is None:
            self._message_dispatcher = MessageDispatcher()
        else:
            self._message_dispatcher = message_dispatcher

        self._mode = mode

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

        if self._mode == ShareEntityCreateMode.KEEP_ID:
            scenario.id = zip_scenario.id
        scenario.title = zip_scenario.title
        scenario.creation_type = ScenarioCreationType.IMPORTED
        scenario.description = zip_scenario.description
        scenario.status = zip_scenario.status

        if zip_scenario.folder is not None:
            folder = SpaceFolder.get_by_id(zip_scenario.folder.id)

            if folder is None:
                self._message_dispatcher.notify_info_message(
                    f"Folder '{zip_scenario.folder.name}' not found, skipping linking scenario to folder.")
            else:
                scenario.folder = folder

        if zip_scenario.error_info is not None:
            scenario.set_error_info(zip_scenario.error_info)

        return scenario

    def _load_protocol_model(self, protocol: ScenarioProtocolDTO) -> ProtocolModel:
        copy_ids: bool = self._mode == ShareEntityCreateMode.KEEP_ID
        protocol_factory = ProtocolGraphFactoryFromConfig(protocol.data, copy_ids)
        return protocol_factory.create_protocol_model()

    def get_scenario(self) -> Scenario:
        if self._scenario is None:
            raise Exception("Scenario not loaded, call load_scenario first")
        return self._scenario

    def get_protocol_model(self) -> ProtocolModel:
        if self._protocol_model is None:
            raise Exception("Protocol model not loaded, call load_scenario first")

        return self._protocol_model

    def get_tags(self) -> List[Tag]:
        return TagHelper.tags_dto_to_list(self.exp_info.scenario.tags)

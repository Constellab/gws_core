from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.folder.space_folder import SpaceFolder
from gws_core.protocol.protocol_dto import ScenarioProtocolDTO
from gws_core.protocol.protocol_graph_factory import ProtocolGraphFactoryFromConfig
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.resource_model_loader import ResourceModelLoader
from gws_core.scenario.scenario import Scenario
from gws_core.scenario.scenario_enums import ScenarioCreationType
from gws_core.scenario.scenario_zipper import ScenarioExportDTO, ScenarioExportPackage
from gws_core.share.shared_dto import ShareEntityCreateMode
from gws_core.tag.tag import Tag
from gws_core.tag.tag_helper import TagHelper
from gws_core.task.task_model import TaskModel


# TODO doesn't work if a task uses a resource typing (input or output) not
# available in the lab. Or if we download a resource that uses a typing not
# available in the lab.
class ScenarioLoader:
    exp_info: ScenarioExportPackage

    _scenario: Scenario
    _protocol_model: ProtocolModel

    _message_dispatcher: MessageDispatcher

    _mode: ShareEntityCreateMode

    def __init__(
        self,
        scenario_info: ScenarioExportPackage,
        mode: ShareEntityCreateMode,
        message_dispatcher: MessageDispatcher | None = None,
    ) -> None:
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

    def _load_scenario(self, zip_scenario: ScenarioExportDTO) -> Scenario:
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
                    f"Folder '{zip_scenario.folder.name}' not found, skipping linking scenario to folder."
                )
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

    def load_resource_models(self, scenario: Scenario) -> dict[str, ResourceModel]:
        """Load ResourceModel objects for all root resources from the export metadata.

        All models are created with content_is_deleted=True. This preserves resource
        information in ports even when the resource content is not downloaded.
        Only root resources (without parent) are included, sub-resources are not handled here.

        The returned models are not saved to the database, the caller is responsible for saving them.

        :param scenario: the scenario to link to the resource models
        :return: dict mapping original resource id to the loaded ResourceModel
        """
        resource_model_dtos = self.exp_info.root_resource_models
        if not resource_model_dtos:
            return {}

        resource_models: dict[str, ResourceModel] = {}

        for dto in resource_model_dtos:
            loader = ResourceModelLoader(dto)
            task_model = (
                self._protocol_model.get_process_by_id(dto.task_model_id)
                if dto.task_model_id
                else None
            )
            if not task_model or not isinstance(task_model, TaskModel):
                raise Exception(
                    f"Task model with id {dto.task_model_id} not found for resource model {dto.id}"
                )
            resource_model = loader.load_resource_model(
                scenario=scenario,
                task_model=task_model,
                origin=ResourceOrigin.IMPORTED_FROM_LAB,
            )
            resource_models[dto.id] = resource_model

        return resource_models

    def get_tags(self) -> list[Tag]:
        return TagHelper.tags_dto_to_list(self.exp_info.scenario.tags)

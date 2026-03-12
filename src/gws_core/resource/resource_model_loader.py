from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.folder.space_folder import SpaceFolder
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.resource.id_mapper import IdMapper
from gws_core.resource.resource_dto import ResourceModelExportDTO, ResourceOrigin
from gws_core.resource.resource_model import ResourceModel
from gws_core.scenario.scenario import Scenario
from gws_core.task.task_model import TaskModel
from gws_core.user.user import User


class ResourceModelLoader:
    """Class to load a ResourceModel from a ResourceModelExportDTO.

    Handles resolving the scenario and task model that generated the resource:
    - If the DTO references the provided scenario, it links to it and looks up
      the task model from the provided protocol model.
    - If the DTO references a different scenario, it tries to find the existing
      scenario and task model in the lab database. If not found, the resource is
      loaded without a scenario/task link and an info message is dispatched.
    """

    _dto: ResourceModelExportDTO
    _message_dispatcher: MessageDispatcher | None
    _id_mapper: IdMapper

    def __init__(
        self,
        dto: ResourceModelExportDTO,
        message_dispatcher: MessageDispatcher | None = None,
        id_mapper: IdMapper | None = None,
    ) -> None:
        self._dto = dto
        self._message_dispatcher = message_dispatcher
        self._id_mapper = id_mapper if id_mapper is not None else IdMapper()

    def load_resource_model(
        self,
        origin: ResourceOrigin | None = None,
    ) -> ResourceModel:
        """Create a ResourceModel from a ResourceModelExportDTO.

        This sets the persistable fields from the DTO. Computed fields like
        is_downloadable, has_children, type_status, and is_application are
        derived at read time and are not stored.

        It resolves the scenario and task model that generated this resource:
        - If the DTO references the provided scenario, it links to it and looks up
          the task model from the provided protocol model.
        - If the DTO references a different scenario, it tries to find the existing
          scenario and task model in the lab database. If not found, the resource is
          loaded without a scenario/task link and an info message is dispatched.
        :param origin: optional origin override, if not provided uses the DTO origin
        :return: the resource model (not yet saved to DB)
        """
        dto = self._dto

        resource_model = ResourceModel()
        resource_model.id = dto.id
        resource_model.created_at = dto.created_at
        resource_model.created_by = User.get_by_id_and_check(dto.created_by.id)
        resource_model.last_modified_at = dto.last_modified_at
        resource_model.last_modified_by = User.get_by_id_and_check(dto.last_modified_by.id)
        resource_model.parent_resource_id = dto.parent_resource_id
        resource_model.content_is_deleted = True

        self.update_resource_model(resource_model, origin)

        return resource_model

    def update_resource_model(
        self,
        resource_model: ResourceModel,
        origin: ResourceOrigin | None = None,
    ) -> ResourceModel:
        """Update shared attributes on an existing ResourceModel from the DTO.

        Sets the same attributes as load_resource_model, excluding create-only
        fields (id, created_at, created_by, last_modified_at, last_modified_by,
        content_is_deleted).

        :param resource_model: the existing resource model to update
        :param origin: optional origin override, if not provided uses the DTO origin
        :return: the updated resource model
        """
        dto = self._dto

        resolved_scenario, resolved_task_model = self._resolve_scenario_and_task()

        resource_model.resource_typing_name = dto.resource_typing_name
        resource_model.name = dto.name
        resource_model.origin = origin if origin is not None else dto.origin
        resource_model.flagged = dto.flagged
        # If SpaceFolder.get_by_id returns None, it is not a problem
        resource_model.folder = SpaceFolder.get_by_id(dto.folder.id) if dto.folder else None
        resource_model.style = dto.style
        resource_model.generated_by_port_name = dto.generated_by_port_name
        resource_model.scenario = resolved_scenario
        resource_model.task_model = resolved_task_model

        return resource_model

    def _resolve_scenario_and_task(
        self,
    ) -> tuple[Scenario | None, TaskModel | None]:
        """Resolve the scenario and task model referenced by the DTO.

        :return: tuple of (resolved_scenario, resolved_task_model)
        """
        dto = self._dto

        if dto.scenario and dto.task_model_id:
            existing_scenario = Scenario.get_by_id(self._resolve_id(dto.scenario.id))
            existing_task = TaskModel.get_by_id(self._resolve_id(dto.task_model_id))

            if existing_scenario and existing_task:
                return existing_scenario, existing_task

            dispatcher = self._message_dispatcher or MessageDispatcher()
            dispatcher.notify_info_message(
                f"Resource model '{dto.name}' references scenario '{dto.scenario.title}' and task model with id '{dto.task_model_id}' which could not be found in the lab. The resource will be loaded without linking it to the scenario and task."
            )

        return None, None

    def _resolve_id(self, old_id: str) -> str:
        """Resolve an old resource ID to the actual DB ID.

        In NEW_ID mode, returns the mapped new ID. In KEEP_ID mode, returns the same ID.
        """
        return self._id_mapper.get_new_id(old_id) or old_id

from __future__ import annotations

from typing import TYPE_CHECKING

from gws_core.folder.space_folder import SpaceFolder
from gws_core.resource.resource_dto import ResourceModelExportDTO, ResourceOrigin
from gws_core.resource.resource_model import ResourceModel
from gws_core.user.user import User

if TYPE_CHECKING:
    from gws_core.scenario.scenario import Scenario
    from gws_core.task.task_model import TaskModel


class ResourceModelLoader:
    """Class to load a ResourceModel from a ResourceModelExportDTO."""

    _dto: ResourceModelExportDTO

    def __init__(self, dto: ResourceModelExportDTO) -> None:
        self._dto = dto

    def load_resource_model(
        self,
        scenario: Scenario | None = None,
        task_model: TaskModel | None = None,
        origin: ResourceOrigin | None = None,
    ) -> ResourceModel:
        """Create a ResourceModel from a ResourceModelExportDTO.

        This sets the persistable fields from the DTO. Computed fields like
        is_downloadable, has_children, type_status, and is_application are
        derived at read time and are not stored.

        :param scenario: the scenario to link to the resource model
        :param task_model: the task model that generated the resource
        :param origin: optional origin override, if not provided uses the DTO origin
        :return: the resource model
        :rtype: ResourceModel
        """
        dto = self._dto
        resource_model = ResourceModel()
        resource_model.id = dto.id
        resource_model.created_at = dto.created_at
        resource_model.created_by = User.get_by_id_and_check(dto.created_by.id)
        resource_model.last_modified_at = dto.last_modified_at
        resource_model.last_modified_by = User.get_by_id_and_check(dto.last_modified_by.id)
        resource_model.resource_typing_name = dto.resource_typing_name
        resource_model.name = dto.name
        resource_model.origin = origin if origin is not None else dto.origin
        resource_model.flagged = dto.flagged
        # If SpaceFolder.get_by_id returns None, it is not a problem
        resource_model.folder = SpaceFolder.get_by_id(dto.folder.id) if dto.folder else None
        resource_model.style = dto.style
        resource_model.parent_resource_id = dto.parent_resource_id
        resource_model.generated_by_port_name = dto.generated_by_port_name
        resource_model.content_is_deleted = True
        resource_model.scenario = scenario
        resource_model.task_model = task_model
        return resource_model

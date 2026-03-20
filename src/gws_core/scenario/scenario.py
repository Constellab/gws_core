from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, final

from peewee import BooleanField, CharField, ForeignKeyField, IntegerField, ModelSelect

from gws_core.core.db.gws_core_db_manager import GwsCoreDbManager
from gws_core.core.model.sys_proc import SysProc
from gws_core.core.utils.date_helper import DateHelper
from gws_core.entity_navigator.entity_navigator_type import NavigableEntity, NavigableEntityType
from gws_core.folder.model_with_folder import ModelWithFolder
from gws_core.impl.rich_text.rich_text_db_field import RichTextDbField
from gws_core.impl.rich_text.rich_text_types import RichTextDTO
from gws_core.lab.lab_config_model import LabConfigModel
from gws_core.lab.lab_model.lab_model import LabModel
from gws_core.process.process_types import ProcessErrorInfo, ProcessStatus
from gws_core.protocol.protocol_dto import ScenarioProtocolDTO
from gws_core.scenario.scenario_dto import ScenarioDTO, ScenarioProgressDTO, ScenarioSimpleDTO
from gws_core.scenario.scenario_zipper import ScenarioExportDTO
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.tag_entity_type import TagEntityType
from gws_core.user.current_user_service import CurrentUserService

from ..core.classes.enum_field import EnumField
from ..core.exception.exceptions import BadRequestException
from ..core.exception.gws_exceptions import GWSException
from ..core.model.db_field import DateTimeUTC, JSONField
from ..core.model.model_with_user import ModelWithUser
from ..folder.space_folder import SpaceFolder
from ..resource.resource_model import ResourceModel
from ..user.user import User
from .scenario_enums import ScenarioCreationType, ScenarioProcessStatus, ScenarioStatus

if TYPE_CHECKING:
    from ..protocol.protocol_model import ProtocolModel
    from ..task.task_model import TaskModel


@final
class Scenario(ModelWithUser, ModelWithFolder, NavigableEntity):
    folder: SpaceFolder = ForeignKeyField(SpaceFolder, null=True)

    status: ScenarioStatus = EnumField(choices=ScenarioStatus, default=ScenarioStatus.DRAFT)
    error_info: dict[str, Any] | None = JSONField(null=True)
    creation_type: ScenarioCreationType = EnumField(
        choices=ScenarioCreationType, default=ScenarioCreationType.MANUAL, max_length=20
    )

    title = CharField(max_length=50)
    description: RichTextDTO = RichTextDbField(null=True)
    lab_config: LabConfigModel | None = ForeignKeyField(LabConfigModel, null=True)

    is_validated: bool = BooleanField(default=False)
    validated_at: datetime | None = DateTimeUTC(null=True)
    validated_by = ForeignKeyField(User, null=True, backref="+")

    # Date of the last synchronisation with space, null if never synchronised
    last_sync_at: datetime | None = DateTimeUTC(null=True)
    last_sync_by = ForeignKeyField(User, null=True, backref="+")

    is_archived = BooleanField(default=False, index=True)
    running_process_pid: int | None = IntegerField(null=True)
    running_in_external_lab: LabModel | None = ForeignKeyField(
        LabModel, null=True, backref="+", on_delete="SET NULL"
    )

    # cache of the _protocol
    _protocol: ProtocolModel | None = None

    @property
    def protocol_model(self) -> ProtocolModel:
        """
        Returns the main protocol model
        """
        from ..protocol.protocol_model import ProtocolModel

        if self._protocol is None:
            self._protocol = ProtocolModel.get(
                (ProtocolModel.scenario == self) & (ProtocolModel.parent_protocol_id.is_null())
            )

        return self._protocol

    def get_task_models(self) -> list[TaskModel]:
        """
        Returns child process models.
        """
        from ..task.task_model import TaskModel

        if not self.is_saved():
            return []

        return list(TaskModel.select().where(TaskModel.scenario == self))

    def get_generated_resources(self) -> list[ResourceModel]:
        """
        Returns child resources.
        """

        if not self.is_saved():
            return []

        return list(ResourceModel.select().where(ResourceModel.scenario == self))

    def get_short_name(self) -> str:
        """Method to get a readable to quickly distinguish the scenario, (used in error message)

        :return: [description]
        :rtype: str
        """
        return self.title

    def get_running_tasks(self) -> list[TaskModel]:
        from ..task.task_model import TaskModel

        return list(
            TaskModel.select().where(
                (TaskModel.scenario == self)
                & (
                    TaskModel.status.in_(
                        [ProcessStatus.RUNNING, ProcessStatus.WAITING_FOR_CLI_PROCESS]
                    )
                )
            )
        )

    def get_current_progress(self) -> ScenarioProgressDTO:
        return self.protocol_model.get_current_progress()

    def get_navigable_entity_name(self) -> str:
        return self.title

    def get_navigable_entity_type(self) -> NavigableEntityType:
        return NavigableEntityType.SCENARIO

    def navigable_entity_is_validated(self) -> bool:
        return self.is_validated

    def is_manual(self) -> bool:
        return self.creation_type == ScenarioCreationType.MANUAL

    ########################################## MODEL METHODS ######################################

    @GwsCoreDbManager.transaction()
    def archive(self, archive: bool) -> Scenario:
        """
        Archive the scenario
        """

        if self.is_archived == archive:
            return self
        self.protocol_model.archive(archive)

        self.is_archived = archive
        return self.save()

    @classmethod
    def count_running_scenarios(cls) -> int:
        """
        :return: the count of scenario in progress or waiting for a cli process
        :rtype: `int`
        """

        return cls.get_running_scenarios().count()

    @classmethod
    def get_running_scenarios(cls) -> ModelSelect:
        """
        :return: the count of scenario in progress or waiting for a cli process
        :rtype: `int`
        """

        return Scenario.select().where(
            (Scenario.status == ScenarioStatus.RUNNING)
            | (Scenario.status == ScenarioStatus.WAITING_FOR_CLI_PROCESS)
            | (Scenario.status == ScenarioStatus.RUNNING_IN_EXTERNAL_LAB)
        )

    @classmethod
    def count_running_or_queued_scenarios(cls) -> int:
        return (
            Scenario.select()
            .where(
                (Scenario.status == ScenarioStatus.RUNNING)
                | (Scenario.status == ScenarioStatus.WAITING_FOR_CLI_PROCESS)
                | (Scenario.status == ScenarioStatus.RUNNING_IN_EXTERNAL_LAB)
                | (Scenario.status == ScenarioStatus.IN_QUEUE)
            )
            .count()
        )

    @classmethod
    def count_queued_scenarios(cls) -> int:
        return Scenario.select().where(Scenario.status == ScenarioStatus.IN_QUEUE).count()

    @GwsCoreDbManager.transaction()
    def reset(self) -> Scenario:
        """
        Reset the scenario.

        :return: True if it is reset, False otherwise
        :rtype: `bool`
        """
        if not self.is_saved():
            raise BadRequestException("Can't reset a scenario not saved before")

        if self.is_running:
            raise BadRequestException("Can't reset a running scenario")

        if self.protocol_model:
            self.protocol_model.reset()

        self.mark_as_draft()
        return self

    @GwsCoreDbManager.transaction()
    def validate(self) -> None:
        """
        Validate the scenario
        """

        if self.is_validated:
            return
        if self.is_running:
            raise BadRequestException(
                GWSException.SCENARIO_VALIDATE_RUNNING.value,
                unique_code=GWSException.SCENARIO_VALIDATE_RUNNING.name,
            )

        if self.folder is None:
            raise BadRequestException(
                "The scenario must be linked to a folder before validating it"
            )

        if self.folder.children.count() > 0:
            raise BadRequestException(
                "The scenario must be associated with a leaf folder (folder with no children)"
            )

        self.is_validated = True
        self.validated_at = DateHelper.now_utc()
        self.validated_by = CurrentUserService.get_and_check_current_user()

    @GwsCoreDbManager.transaction()
    def delete_instance(self, *args, **kwargs):
        self.reset()

        if self.protocol_model:
            self.protocol_model.delete_instance()

        super().delete_instance(*args, **kwargs)
        EntityTagList.delete_by_entity(TagEntityType.SCENARIO, self.id)

    @classmethod
    def get_synced_objects(cls) -> list[Scenario]:
        """Get all scenarios that are synced with space

        :return: [description]
        :rtype: [type]
        """
        return list(cls.select().where(cls.last_sync_at.is_null(False)))

    @classmethod
    def clear_folder(cls, folders: list[SpaceFolder]) -> None:
        cls.update(folder=None, last_sync_at=None, last_sync_by=None).where(
            cls.folder.in_(folders)
        ).execute()

    ########################### STATUS MANAGEMENT ##################################

    @property
    def is_success(self) -> bool:
        return self.status == ScenarioStatus.SUCCESS

    @property
    def is_finished(self) -> bool:
        """Consider finished if the Scenario status is SUCCESS or ERROR"""
        return self.is_success or self.is_error

    @property
    def is_running(self) -> bool:
        """Consider running if the Scenario status is RUNNING or WAITING_FOR_CLI_PROCESS"""
        return self.status in (
            ScenarioStatus.RUNNING,
            ScenarioStatus.WAITING_FOR_CLI_PROCESS,
            ScenarioStatus.RUNNING_IN_EXTERNAL_LAB,
        )

    @property
    def is_running_or_waiting(self) -> bool:
        """Consider running if the Scenario status is RUNNING or WAITING_FOR_CLI_PROCESS"""
        return self.is_running or self.status == ScenarioStatus.IN_QUEUE

    @property
    def is_error(self) -> bool:
        """Consider running if the Scenario status is RUNNING or WAITING_FOR_CLI_PROCESS"""
        return self.status == ScenarioStatus.ERROR

    @property
    def is_draft(self) -> bool:
        return self.status == ScenarioStatus.DRAFT

    @property
    def is_partially_run(self) -> bool:
        return self.status == ScenarioStatus.PARTIALLY_RUN

    @property
    def is_running_in_external_lab(self) -> bool:
        return self.status == ScenarioStatus.RUNNING_IN_EXTERNAL_LAB

    def mark_as_in_queue(self):
        self.status = ScenarioStatus.IN_QUEUE
        self.save()

    def mark_as_waiting_for_cli_process(self, pid: int):
        """Mark that a process is created for the scenario, but it is not started yet

        :param pid: pid of the linux process
        :type pid: int
        """
        self.status = ScenarioStatus.WAITING_FOR_CLI_PROCESS
        self.running_process_pid = pid
        self.save()

    def mark_as_started(self, pid: int):
        self.status = ScenarioStatus.RUNNING
        self.lab_config = LabConfigModel.get_current_config()
        self.running_process_pid = pid
        self.save()

    def mark_as_success(self):
        self._clear_running_info()
        self.status = ScenarioStatus.SUCCESS
        self.save()

    def mark_as_draft(self):
        self._clear_running_info()
        self.status = ScenarioStatus.DRAFT
        self.lab_config = None
        self.set_error_info(None)
        self.save()

    def mark_as_error(self, error_info: ProcessErrorInfo) -> None:
        if self.is_error:
            return
        self._clear_running_info()
        self.status = ScenarioStatus.ERROR
        self.set_error_info(error_info)
        self.save()

        # mark the protocol as error if it is not already
        if not self.protocol_model.is_error:
            self.protocol_model.mark_as_error(error_info)

    def mark_as_partially_run(self) -> None:
        self.status = ScenarioStatus.PARTIALLY_RUN
        self._clear_running_info()
        self.set_error_info(None)
        self.save()

    def mark_as_running_in_external_lab(self, lab: LabModel) -> None:
        """Mark the scenario as being processed in an external lab."""
        self.status = ScenarioStatus.RUNNING_IN_EXTERNAL_LAB
        self.running_in_external_lab = lab
        self.save()

    def _clear_running_info(self) -> None:
        """Clear the running info of the scenario (used when the scenario is stopped or when an error occurs)"""
        self.running_process_pid = None
        self.running_in_external_lab = None

    def get_error_info(self) -> ProcessErrorInfo | None:
        return ProcessErrorInfo.from_json(self.error_info) if self.error_info else None

    def set_error_info(self, error_info: ProcessErrorInfo | None) -> None:
        self.error_info = error_info.to_json_dict() if error_info else None

    def check_is_stopable(self) -> None:
        """Throw an error if the scenario is not stopable"""

        # check scenario status
        if not self.is_running:
            raise BadRequestException(detail=f"Scenario '{self.id}' is not running")

    def check_is_updatable(self) -> None:
        """Throw an error if the scenario is not updatable"""

        # check scenario status
        if self.is_validated:
            raise BadRequestException(detail="The scenario is validated, you can't update it")
        if self.is_archived:
            raise BadRequestException(
                detail="The scenario is archived, please unachived it to update it"
            )

    def copy_from_and_save(self, other: Scenario) -> None:
        """Copy metadata fields from another Scenario and save."""
        self.title = other.title
        self.description = other.description
        # Don't update status if the scenario is running in an external lab
        # and the other scenario is not finished,
        # so in this case we keep the RUNNING_IN_EXTERNAL_LAB
        if not self.is_running_in_external_lab or not other.is_running_or_waiting:
            self.status = other.status
        self.error_info = other.error_info
        if other.folder:
            self.folder = other.folder
        self.save()

    def get_process_status(self) -> ScenarioProcessStatus:
        if self.running_process_pid is None or not self.is_running:
            return ScenarioProcessStatus.NONE
        try:
            process = SysProc.from_pid(self.running_process_pid)
            if process.is_alive():
                return ScenarioProcessStatus.RUNNING
            else:
                return ScenarioProcessStatus.UNEXPECTED_STOPPED
        except Exception:
            return ScenarioProcessStatus.UNEXPECTED_STOPPED

    ########################### TO JSON ##################################

    def to_dto(self) -> ScenarioDTO:
        return ScenarioDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            created_by=self.created_by.to_dto(),
            last_modified_by=self.last_modified_by.to_dto(),
            title=self.title,
            description=self.description,
            creation_type=self.creation_type,
            protocol={"id": self.protocol_model.id},
            status=self.status,
            is_validated=self.is_validated,
            validated_by=self.validated_by.to_dto() if self.validated_by else None,
            validated_at=self.validated_at,
            last_sync_by=self.last_sync_by.to_dto() if self.last_sync_by else None,
            last_sync_at=self.last_sync_at,
            is_archived=self.is_archived,
            folder=self.folder.to_dto() if self.folder else None,
            pid_status=self.get_process_status(),
        )

    def to_scenario_export_dto(self) -> ScenarioExportDTO:
        scenario_tags = EntityTagList.find_by_entity(TagEntityType.SCENARIO, self.id)
        tags_dtos = [tag.to_simple_tag().to_dto() for tag in scenario_tags.get_tags()]

        # Derive status from protocol model when locked, so the destination lab
        # doesn't inherit RUNNING_IN_EXTERNAL_LAB
        if self.is_running_in_external_lab:
            protocol_status = self.protocol_model.status
            status_map = {
                ProcessStatus.DRAFT: ScenarioStatus.DRAFT,
                ProcessStatus.SUCCESS: ScenarioStatus.SUCCESS,
                ProcessStatus.ERROR: ScenarioStatus.ERROR,
                ProcessStatus.PARTIALLY_RUN: ScenarioStatus.PARTIALLY_RUN,
            }
            export_status = status_map.get(protocol_status, ScenarioStatus.DRAFT)
        else:
            export_status = self.status

        return ScenarioExportDTO(
            id=self.id,
            title=self.title,
            description=self.description,
            status=export_status,
            folder=self.folder.to_dto() if self.folder else None,
            error_info=self.get_error_info(),
            tags=tags_dtos,
        )

    def to_simple_dto(self) -> ScenarioSimpleDTO:
        return ScenarioSimpleDTO(id=self.id, title=self.title)

    def export_protocol(self) -> ScenarioProtocolDTO:
        return ScenarioProtocolDTO(
            data=self.protocol_model.to_config_dto(),
        )

    class Meta:
        table_name = "gws_scenario"
        is_table = True

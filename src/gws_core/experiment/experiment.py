# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, final

from peewee import (BooleanField, CharField, DoubleField, ForeignKeyField,
                    ModelSelect)

from gws_core.core.model.sys_proc import SysProc
from gws_core.core.utils.date_helper import DateHelper
from gws_core.entity_navigator.entity_navigator_type import (EntityType,
                                                             NavigableEntity)
from gws_core.experiment.experiment_dto import (ExperimentDTO,
                                                ExperimentSimpleDTO)
from gws_core.lab.lab_config_model import LabConfigModel
from gws_core.process.process_types import ProcessErrorInfo, ProcessStatus
from gws_core.project.model_with_project import ModelWithProject
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.user.current_user_service import CurrentUserService

from ..core.classes.enum_field import EnumField
from ..core.decorator.transaction import transaction
from ..core.exception.exceptions import BadRequestException
from ..core.exception.gws_exceptions import GWSException
from ..core.model.db_field import DateTimeUTC, JSONField
from ..core.model.model_with_user import ModelWithUser
from ..project.project import Project
from ..resource.resource_model import ResourceModel
from ..tag.taggable_model import TaggableModel
from ..user.user import User
from .experiment_enums import (ExperimentProcessStatus, ExperimentStatus,
                               ExperimentType)

if TYPE_CHECKING:
    from ..protocol.protocol_model import ProtocolModel
    from ..task.task_model import TaskModel


@final
class Experiment(ModelWithUser, TaggableModel, ModelWithProject, NavigableEntity):
    """
    Experiment class.

    :property project: The project of the experiment
    :type project: `gws.project.Project`
    :property protocol: The the protocol of the experiment
    :type protocol: `gws_core.protocol.protocol.Protocol`
    :property created_by: The user who created the experiment. This user may be different from the user who runs the experiment.
    :type created_by: `gws.user.User`
    :property score: The score of the experiment
    :type score: `float`
    :property is_validated: True if the experiment is validated, False otherwise. Defaults to False.
    :type is_validated: `bool`
    """

    project: Project = ForeignKeyField(Project, null=True)

    score = DoubleField(null=True)
    status: ExperimentStatus = EnumField(choices=ExperimentStatus,
                                         default=ExperimentStatus.DRAFT)
    error_info: ProcessErrorInfo = JSONField(null=True)
    type: ExperimentType = EnumField(choices=ExperimentType,
                                     default=ExperimentType.EXPERIMENT)

    title = CharField(max_length=50)
    description = JSONField(null=True)
    lab_config: LabConfigModel = ForeignKeyField(LabConfigModel, null=True)

    is_validated: bool = BooleanField(default=False)
    validated_at: datetime = DateTimeUTC(null=True)
    validated_by = ForeignKeyField(User, null=True, backref='+')

    # Date of the last synchronisation with space, null if never synchronised
    last_sync_at = DateTimeUTC(null=True)
    last_sync_by = ForeignKeyField(User, null=True, backref='+')

    is_archived = BooleanField(default=False, index=True)
    data: Dict[str, Any] = JSONField(null=True)

    _table_name = 'gws_experiment'

    # cache of the _protocol
    _protocol: ProtocolModel = None

    @property
    def pid(self) -> int:
        if "pid" not in self.data:
            return None
        return self.data["pid"]

    @pid.setter
    def pid(self, value: int):
        self.data["pid"] = value

    @property
    def protocol_model(self) -> ProtocolModel:
        """
        Returns the main protocol model
        """
        from ..protocol.protocol_model import ProtocolModel

        if self._protocol is None:
            self._protocol = ProtocolModel.get((ProtocolModel.experiment == self)
                                               & (ProtocolModel.parent_protocol_id.is_null()))

        return self._protocol

    @property
    def task_models(self) -> List[TaskModel]:
        """
        Returns child process models.
        """
        from ..task.task_model import TaskModel
        if not self.is_saved():
            return []

        return list(TaskModel.select().where(
            TaskModel.experiment == self))

    @property
    def resources(self) -> List[ResourceModel]:
        """
        Returns child resources.
        """

        if not self.is_saved():
            return []

        return list(ResourceModel.select().where(ResourceModel.experiment == self))

    def get_short_name(self) -> str:
        """Method to get a readable to quickly distinguish the experiment, (used in error message)

        :return: [description]
        :rtype: str
        """
        return self.title

    def check_user_privilege(self, user: User) -> None:
        return self.protocol_model.check_user_privilege(user)

    def get_running_tasks(self) -> List[TaskModel]:
        from ..task.task_model import TaskModel
        return list(TaskModel.select().where(
            (TaskModel.experiment == self) &
            (TaskModel.status.in_([ProcessStatus.RUNNING, ProcessStatus.WAITING_FOR_CLI_PROCESS]))))

    def get_entity_name(self) -> str:
        return self.title

    def get_entity_type(self) -> EntityType:
        return EntityType.EXPERIMENT

    ########################################## MODEL METHODS ######################################

    @transaction()
    def archive(self, archive: bool) -> 'Experiment':
        """
        Archive the experiment
        """

        if self.is_archived == archive:
            return self
        self.protocol_model.archive(archive)

        return super().archive(archive)

    @classmethod
    def count_running_experiments(cls) -> int:
        """
        :return: the count of experiment in progress or waiting for a cli process
        :rtype: `int`
        """

        return cls.get_running_experiments().count()

    @classmethod
    def get_running_experiments(cls) -> ModelSelect:
        """
        :return: the count of experiment in progress or waiting for a cli process
        :rtype: `int`
        """

        return Experiment.select().where((Experiment.status == ExperimentStatus.RUNNING) |
                                         (Experiment.status == ExperimentStatus.WAITING_FOR_CLI_PROCESS))

    @classmethod
    def count_running_or_queued_experiments(cls) -> int:
        return Experiment.select().where((Experiment.status == ExperimentStatus.RUNNING) |
                                         (Experiment.status == ExperimentStatus.IN_QUEUE) |
                                         (Experiment.status == ExperimentStatus.WAITING_FOR_CLI_PROCESS)).count()

    @classmethod
    def count_queued_experiments(cls) -> int:
        return Experiment.select().where((Experiment.status == ExperimentStatus.IN_QUEUE)).count()

    @transaction()
    def reset(self) -> 'Experiment':
        """
        Reset the experiment.

        :return: True if it is reset, False otherwise
        :rtype: `bool`
        """
        from gws_core.report.report_view_model import ReportViewModel

        from ..task.task_input_model import TaskInputModel

        if not self.is_saved():
            raise BadRequestException(
                "Can't reset an experiment not saved before")

        if self.is_validated or self.is_archived:
            raise BadRequestException(
                "Can't reset a validated or archived experiment")

        if self.is_running:
            raise BadRequestException("Can't reset a running experiment")

        # Check if any resource of this experiment is used in another one
        output_resources: List[ResourceModel] = list(
            ResourceModel.get_by_experiment(self.id))
        ResourceModel.check_if_any_resource_is_used_in_another_exp(
            output_resources, self.id)

        # check if any resource of this experiment is used in a report
        resource_ids = [r.id for r in output_resources]
        report_view_models: List[ReportViewModel] = list(ReportViewModel.get_by_resources(resource_ids))
        if len(report_view_models) > 0:
            report_names = list({r.report.title for r in report_view_models})
            raise BadRequestException(
                f"Can't reset an experiment because the report(s) {report_names} are using some resource(s) of this experiment")

        if self.protocol_model:
            self.protocol_model.reset()

        # Delete all the resources previously generated to clear the DB
        ResourceModel.delete_multiple_resources(output_resources)

        # Delete all the TaskInput as well
        # Most of them are deleted when deleting the resource but for some constant inputs (link source)
        # the resource is not deleted but the input must be deleted
        TaskInputModel.delete_by_experiment(self.id)

        self.mark_as_draft()
        return self

    @transaction()
    def validate(self) -> None:
        """
        Validate the experiment
        """

        if self.is_validated:
            return
        if self.is_running:
            raise BadRequestException(GWSException.EXPERIMENT_VALIDATE_RUNNING.value,
                                      unique_code=GWSException.EXPERIMENT_VALIDATE_RUNNING.name)

        if self.project is None:
            raise BadRequestException(
                "The experiment must be linked to a project before validating it")

        if self.project.children.count() > 0:
            raise BadRequestException(
                "The experiment must be associated with a leaf project (project with no children)")

        self.is_validated = True
        self.validated_at = DateHelper.now_utc()
        self.validated_by = CurrentUserService.get_and_check_current_user()

    @transaction()
    def delete_instance(self, *args, **kwargs):
        self.reset()

        if self.protocol_model:
            self.protocol_model.delete_instance()

        super().delete_instance(*args, **kwargs)
        EntityTagList.delete_by_entity(EntityType.EXPERIMENT, self.id)

    @classmethod
    def after_table_creation(cls) -> None:
        super().after_table_creation()
        cls.create_full_text_index(['title', 'description'], 'I_F_EXP_TIDESC')

    ########################### STATUS MANAGEMENT ##################################

    @property
    def is_success(self) -> bool:
        return self.status == ExperimentStatus.SUCCESS

    @property
    def is_finished(self) -> bool:
        """Consider finished if the Experiment status is SUCCESS or ERROR
        """
        return self.is_success or self.is_error

    @property
    def is_running(self) -> bool:
        """Consider running if the Experiment status is RUNNING or WAITING_FOR_CLI_PROCESS
        """
        return self.status == ExperimentStatus.RUNNING or self.status == ExperimentStatus.WAITING_FOR_CLI_PROCESS

    @property
    def is_error(self) -> bool:
        """Consider running if the Experiment status is RUNNING or WAITING_FOR_CLI_PROCESS
        """
        return self.status == ExperimentStatus.ERROR

    @property
    def is_draft(self) -> bool:
        return self.status == ExperimentStatus.DRAFT

    @property
    def is_partially_run(self) -> bool:
        return self.status == ExperimentStatus.PARTIALLY_RUN

    def mark_as_in_queue(self):
        self.status = ExperimentStatus.IN_QUEUE
        self.save()

    def mark_as_waiting_for_cli_process(self, pid: int):
        """Mark that a process is created for the experiment, but it is not started yet

        :param pid: pid of the linux process
        :type pid: int
        """
        self.status = ExperimentStatus.WAITING_FOR_CLI_PROCESS
        self.pid = pid
        self.save()

    def mark_as_started(self, pid: int):
        self.status = ExperimentStatus.RUNNING
        self.lab_config = LabConfigModel.get_current_config()
        self.pid = pid
        self.save()

    def mark_as_success(self):
        self.pid = None
        self.status = ExperimentStatus.SUCCESS
        self.save()

    def mark_as_draft(self):
        self.pid = None
        self.score = None
        self.status = ExperimentStatus.DRAFT
        self.lab_config = None
        self.error_info = None
        self.save()

    def mark_as_error(self, error_info: ProcessErrorInfo) -> None:
        if self.is_error:
            return
        self.pid = None
        self.status = ExperimentStatus.ERROR
        self.error_info = error_info
        self.save()

    def mark_as_partially_run(self) -> None:
        self.status = ExperimentStatus.PARTIALLY_RUN
        self.error_info = None
        self.save()

    def check_is_runnable(self) -> None:
        """Throw an error if the experiment is not runnable
        """

        # check experiment status
        if self.is_archived:
            raise BadRequestException("The experiment is archived")
        if self.is_validated:
            raise BadRequestException("The experiment is validated")
        if self.status == ExperimentStatus.RUNNING:
            raise BadRequestException("The experiment is already running")
        if self.is_success:
            raise BadRequestException("The experiment is already finished")

        # if this is a start and stop, we check that the lab
        # is in the same version as the experiment
        if not self.is_draft and self.lab_config:
            current_lab_config = LabConfigModel.get_current_config()
            if not current_lab_config.is_compatible_with(self.lab_config):
                raise BadRequestException(GWSException.EXP_CONTINUE_LAB_INCOMPATIBLE.value,
                                          unique_code=GWSException.EXP_CONTINUE_LAB_INCOMPATIBLE.name)

    def check_is_stopable(self) -> None:
        """Throw an error if the experiment is not stopable
        """

        # check experiment status
        if not self.is_running:
            raise BadRequestException(
                detail=f"Experiment '{self.id}' is not running")

    def check_is_updatable(self) -> None:
        """Throw an error if the experiment is not updatable
        """

        # check experiment status
        if self.is_validated:
            raise BadRequestException(
                detail="The experiment is validated, you can't update it")
        if self.is_archived:
            raise BadRequestException(
                detail="The experiment is archived, please unachived it to update it")

    def get_process_status(self) -> ExperimentProcessStatus:
        if self.pid == None or not self.is_running:
            return ExperimentProcessStatus.NONE
        try:
            process = SysProc.from_pid(self.pid)
            if process.is_alive():
                return ExperimentProcessStatus.RUNNING
            else:
                return ExperimentProcessStatus.UNEXPECTED_STOPPED
        except Exception:
            return ExperimentProcessStatus.UNEXPECTED_STOPPED

    ########################### TO JSON ##################################

    def to_json(self, deep: bool = False, **kwargs) -> dict:
        return self.to_dto()

    def to_dto(self) -> ExperimentDTO:
        return ExperimentDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            created_by=self.created_by.to_dto(),
            last_modified_by=self.last_modified_by.to_dto(),
            title=self.title,
            description=self.description,
            type=self.type,
            protocol={
                "id": self.protocol_model.id
            },
            status=self.status,
            is_validated=self.is_validated,
            validated_by=self.validated_by.to_dto() if self.validated_by else None,
            validated_at=self.validated_at,
            last_sync_by=self.last_sync_by.to_dto() if self.last_sync_by else None,
            last_sync_at=self.last_sync_at,
            is_archived=self.is_archived,
            project=self.project.to_dto() if self.project else None,
            pid_status=self.get_process_status()
        )

    def to_simple_dto(self) -> ExperimentSimpleDTO:
        return ExperimentSimpleDTO(
            id=self.id,
            title=self.title
        )

    def export_protocol(self) -> dict:
        json_ = self.protocol_model.export_config()
        # remove the main instance name because it is not relevant
        del json_["instance_name"]
        return {
            "version": 1,  # version of the protocol json format
            "data": json_
        }

    class Meta:
        table_name = 'gws_experiment'

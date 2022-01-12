# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, List, TypedDict, final

from peewee import (BooleanField, CharField, DoubleField, ForeignKeyField,
                    TextField)

from ..core.classes.enum_field import EnumField
from ..core.decorator.transaction import transaction
from ..core.exception.exceptions import BadRequestException
from ..core.exception.gws_exceptions import GWSException
from ..core.model.json_field import JSONField
from ..core.model.model_with_user import ModelWithUser
from ..core.model.sys_proc import SysProc
from ..core.utils.logger import Logger
from ..model.typing_register_decorator import typing_registrator
from ..project.project import Project
from ..resource.resource_model import ResourceModel
from ..tag.taggable_model import TaggableModel
from ..user.activity import Activity
from ..user.user import User
from .experiment_exception import ResourceUsedInAnotherExperimentException

if TYPE_CHECKING:
    from ..protocol.protocol_model import ProtocolModel
    from ..task.task_model import TaskModel


class ExperimentStatus(Enum):
    DRAFT = "DRAFT"
    # WAITING means that a shell process will be started to run the experiment
    WAITING_FOR_CLI_PROCESS = "WAITING_FOR_CLI_PROCESS"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"


class ExperimentType(Enum):
    # Basic experiment
    EXPERIMENT = "EXPERIMENT"
    # specific experiment generated form a transformer task
    TRANSFORMER = "TRANSFORMER"
    # specific experiment generated form a importer task
    IMPORTER = "IMPORTER"


class ExperimentErrorInfo(TypedDict):
    detail: str
    unique_code: str
    context: str
    instance_id: str


@final
@typing_registrator(unique_name="Experiment", object_type="MODEL", hide=True)
class Experiment(ModelWithUser, TaggableModel):
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
    is_validated: bool = BooleanField(default=False)
    error_info: ExperimentErrorInfo = JSONField(null=True)
    type: ExperimentType = EnumField(choices=ExperimentType,
                                     default=ExperimentType.EXPERIMENT)

    title = CharField(max_length=50)
    description = JSONField(null=True)

    _table_name = 'gws_experiment'

    # cache of the _protocol
    _protocol: ProtocolModel = None

    @property
    def is_pid_alive(self) -> bool:
        if not self.pid:
            raise BadRequestException("No such process found")

        try:
            sproc = SysProc.from_pid(self.pid)
            return sproc.is_alive()
        except Exception as err:
            raise BadRequestException(
                f"No such process found or its access is denied (pid = {self.pid})") from err

    @property
    def pid(self) -> int:
        if "pid" not in self.data:
            return 0
        return self.data["pid"]

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

    ########################################## MODEL METHODS ######################################

    @transaction()
    def archive(self, archive: bool, archive_resources=True) -> 'Experiment':
        """
        Archive the experiment
        """

        if self.is_archived == archive:
            return self
        Activity.add(
            Activity.ARCHIVE,
            object_type=self.full_classname(),
            object_id=self.id
        )
        self.protocol_model.archive(archive, archive_resources=archive_resources)

        return super().archive(archive)

    @classmethod
    def count_of_running_experiments(cls) -> int:
        """
        :return: the count of experiment in progress or waiting for a cli process
        :rtype: `int`
        """

        return Experiment.select().where((Experiment.status == ExperimentStatus.RUNNING) |
                                         (Experiment.status == ExperimentStatus.WAITING_FOR_CLI_PROCESS)).count()

    @transaction()
    def reset(self) -> 'Experiment':
        """
        Reset the experiment.

        :return: True if it is reset, False otherwise
        :rtype: `bool`
        """
        from ..task.task_input_model import TaskInputModel

        if not self.is_saved():
            raise BadRequestException("Can't reset an experiment not saved before")

        if self.is_validated or self.is_archived:
            raise BadRequestException("Can't reset a validated or archived experiment")

        # Check if any resource of this experiment is used in another one
        output_resources: List[ResourceModel] = list(ResourceModel.get_by_experiment(self.id))

        if len(output_resources) > 0:
            output_resource_ids: List[str] = list(map(lambda x: x.id, output_resources))

            other_experiment: TaskInputModel = TaskInputModel.get_other_experiments(
                output_resource_ids, self.id).first()

            if other_experiment is not None:
                raise ResourceUsedInAnotherExperimentException(
                    other_experiment.resource_model.id, other_experiment.experiment.get_short_name())

        if self.protocol_model:
            self.protocol_model.reset()

        # Delete all the resources previously generated to clear the DB
        for output_resource in output_resources:
            output_resource.delete_instance()

        # Delete all the TaskInput as well
        # Most of them are deleted when deleting the resource but for some constant inputs (link source)
        # the resource is not deleted but the input must be deleted
        TaskInputModel.delete_by_experiment(self.id)

        self.status = ExperimentStatus.DRAFT
        self.score = None
        return self.save()

    @transaction()
    def save(self, *args, **kwargs) -> 'Experiment':
        if not self.is_saved():
            Activity.add(
                Activity.CREATE,
                object_type=self.full_classname(),
                object_id=self.id
            )
        return super().save(*args, **kwargs)

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
            raise BadRequestException("The experiment must be linked to a project before validating it")

        self.is_validated = True
        self.save()

    @classmethod
    def create_table(cls, *args, **kwargs):
        if cls.table_exists():
            return
        super().create_table(*args, **kwargs)

        cls.create_full_text_index(['title', 'description'], 'I_F_EXP_TIDESC')

    ########################### STATUS MANAGEMENT ##################################

    @property
    def is_finished(self) -> bool:
        """Consider finished if the Experiment status is SUCCESS or ERROR
        """
        return self.status == ExperimentStatus.SUCCESS or self.is_error

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

    def mark_as_waiting_for_cli_process(self, pid: int):
        """Mark that a process is created for the experiment, but it is not started yet

        :param pid: pid of the linux process
        :type pid: int
        """
        self.status = ExperimentStatus.WAITING_FOR_CLI_PROCESS
        self.data["pid"] = pid
        self.save()

    def mark_as_started(self):
        self.status = ExperimentStatus.RUNNING
        self.save()

    def mark_as_success(self):
        self.data["pid"] = 0
        self.status = ExperimentStatus.SUCCESS
        self.save()

    def mark_as_error(self, error_info: ExperimentErrorInfo) -> None:
        if self.is_error:
            return
        self.data["pid"] = 0
        self.status = ExperimentStatus.ERROR
        self.error_info = error_info
        Logger.error(error_info)
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

    def check_is_stopable(self) -> None:
        """Throw an error if the experiment is not stopable
        """

        # check experiment status
        if not self.is_running:
            raise BadRequestException(detail=f"Experiment '{self.id}' is not running")

    def check_is_updatable(self) -> None:
        """Throw an error if the experiment is not updatable
        """

        # check experiment status
        if self.is_validated:
            raise BadRequestException(
                detail="Experiment is validated, you can't update it")
        if self.is_archived:
            raise BadRequestException(
                detail="Experiment is archived, please unachived it to update it")

    ########################### TO JSON ##################################

    def to_json(self, deep: bool = False, **kwargs) -> dict:
        """
        Returns JSON string or dictionnary representation of the experiment.

        :param stringify: If True, returns a JSON string. Returns a python dictionary otherwise. Defaults to False
        :type stringify: bool
        :param prettify: If True, indent the JSON string. Defaults to False.
        :type prettify: bool
        :return: The representation
        :rtype: dict, str
        """

        _json = super().to_json(deep=deep, **kwargs)

        _json["tags"] = self.get_tags_json()
        _json.update({
            "protocol": {
                "id": self.protocol_model.id,
                "typing_name": self.protocol_model.process_typing_name
            },
        })

        if deep:
            _json["project"] = self.project.to_json() if self.project is not None else None

        return _json

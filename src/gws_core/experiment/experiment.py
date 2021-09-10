# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, List, TypedDict, final

from peewee import BooleanField, FloatField, ForeignKeyField

from ..core.classes.enum_field import EnumField
from ..core.decorator.transaction import transaction
from ..core.exception.exceptions import BadRequestException
from ..core.model.json_field import JSONField
from ..core.model.sys_proc import SysProc
from ..model.typing_register_decorator import typing_registrator
from ..model.viewable import Viewable
from ..resource.experiment_resource import ExperimentResource
from ..resource.resource_model import ResourceModel
from ..study.study import Study
from ..user.activity import Activity
from ..user.user import User

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


class ExperimentErrorInfo(TypedDict):
    detail: str
    unique_code: str
    context: str
    instance_id: str


@final
@typing_registrator(unique_name="Experiment", object_type="MODEL", hide=True)
class Experiment(Viewable):
    """
    Experiment class.

    :property study: The study of the experiment
    :type study: `gws.study.Study`
    :property protocol: The the protocol of the experiment
    :type protocol: `gws_core.protocol.protocol.Protocol`
    :property created_by: The user who created the experiment. This user may be different from the user who runs the experiment.
    :type created_by: `gws.user.User`
    :property score: The score of the experiment
    :type score: `float`
    :property is_validated: True if the experiment is validated, False otherwise. Defaults to False.
    :type is_validated: `bool`
    """

    study = ForeignKeyField(
        Study, null=True, index=True, backref='experiments')

    created_by = ForeignKeyField(
        User, null=True, index=True, backref='created_experiments')
    score = FloatField(null=True, index=True)
    status: ExperimentStatus = EnumField(choices=ExperimentStatus,
                                         default=ExperimentStatus.DRAFT)
    is_validated = BooleanField(default=False, index=True)
    error_info: ExperimentErrorInfo = JSONField(null=True)

    _table_name = 'gws_experiment'

    # backup of the _protocol
    _protocol: ProtocolModel = None

    # -- A --

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
            object_uri=self.uri
        )
        self.protocol_model.archive(archive, archive_resources=archive_resources)

        return super().archive(archive)

    # -- C --

    @classmethod
    def count_of_running_experiments(cls) -> int:
        """
        :return: the count of experiment in progress or waiting for a cli process
        :rtype: `int`
        """

        return Experiment.select().where((Experiment.status == ExperimentStatus.RUNNING) |
                                         (Experiment.status == ExperimentStatus.WAITING_FOR_CLI_PROCESS)).count()

    # -- G --

    def get_title(self) -> str:
        """
        Get the title of the experiment. The title is same as the title of the protocol.

        :rtype: `str`
        """

        return self.data.get("title", "")

    def get_description(self) -> str:
        """
        Get the description of the experiment. The description is same as the title of the protocol

        :rtype: `str`
        """

        return self.data.get("description", "")

    # -- I --

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

    # -- J --

    # -- P --

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
        if not self.id:
            return []

        return list(TaskModel.select().where(
            TaskModel.experiment == self))

    # -- R --

    @property
    def resources(self) -> List[ResourceModel]:
        """
        Returns child resources.
        """

        resources = []
        if self.id:
            Qrel = ExperimentResource.select().where(
                ExperimentResource.experiment_id == self.id)
            for rel in Qrel:
                resources.append(rel.resource)  # is automatically casted
        return resources

    @transaction()
    def reset(self) -> 'Experiment':
        """
        Reset the experiment.

        :return: True if it is reset, False otherwise
        :rtype: `bool`
        """

        if self.is_validated or self.is_archived:
            return None

        if self.protocol_model:
            self.protocol_model.reset()

        self.status = ExperimentStatus.DRAFT
        self.score = None
        return self.save()

    # -- S --

    def set_title(self, title: str) -> None:
        """
        Set the title of the experiment. This title is set to the protocol.

        :param title: The title
        :type title: `str`
        """

        self.data["title"] = title

    def set_description(self, description: str) -> None:
        """
        Get the description of the experiment. This description is set to the protocol.

        :param description: The description
        :type description: `str`
        """

        self.data["description"] = description

    @transaction()
    def save(self, *args, **kwargs) -> 'Experiment':
        if not self.is_saved():
            Activity.add(
                Activity.CREATE,
                object_type=self.full_classname(),
                object_uri=self.uri
            )
        return super().save(*args, **kwargs)

    # -- T --

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
        _json.update({
            "study": {"uri": self.study.uri},
            "protocol": {
                "uri": self.protocol_model.uri,
                "typing_name": self.protocol_model.process_typing_name
            },
            "status": self.status
        })

        return _json

    @transaction()
    def validate(self, user: User) -> None:
        """
        Validate the experiment

        :param user: The user who validate the experiment
        :type user: `gws.user.User`
        """

        if self.is_validated:
            return
        if self.is_running:
            raise BadRequestException("Can't validate a running experiment")
        self.is_validated = True
        if self.save():
            Activity.add(
                Activity.VALIDATE,
                object_type=self.full_classname(),
                object_uri=self.uri,
                user=user
            )

    def check_user_privilege(self, user: User) -> None:
        return self.protocol_model.check_user_privilege(user)

    # -- V --

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
        # self.data["pid"] = 0. /!\ Do not reset pid here, otherwise the experiment could not be stopped if started through cli !!!
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
        if self.status != ExperimentStatus.RUNNING:
            raise BadRequestException(
                detail=f"Experiment '{self.uri}' is not running")

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

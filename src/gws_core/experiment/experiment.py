# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
from enum import Enum
from typing import List, Union

from peewee import BooleanField, FloatField, ForeignKeyField

from ..core.classes.enum_field import EnumField
from ..core.exception.exceptions import BadRequestException
from ..core.model.sys_proc import SysProc
from ..core.utils.event import EventListener
from ..core.utils.http_helper import HTTPHelper
from ..model.viewable import Viewable
from ..protocol.protocol import Protocol
from ..study.study import Study
from ..user.activity import Activity
from ..user.current_user_service import CurrentUserService
from ..user.user import User


class ExperimentStatus(Enum):
    DRAFT = "DRAFT"
    WAITING_FOR_CLI_PROCESS = "WAITING_FOR_CLI_PROCESS"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"


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
    protocol = ForeignKeyField(Protocol, null=True, index=True, backref='+')
    created_by = ForeignKeyField(
        User, null=True, index=True, backref='created_experiments')
    score = FloatField(null=True, index=True)
    # status = EnumField(null=False, choices=ExperimentStatus)
    is_validated = BooleanField(default=False, index=True)

    _is_running = BooleanField(default=False, index=True)
    _is_finished = BooleanField(default=False, index=True)
    _is_success = BooleanField(default=False, index=True)
    _event_listener: EventListener = None
    _table_name = 'gws_experiment'

    def __init__(self, *args, user: User = None, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.id:
            self.data["pid"] = 0
            if user is None:
                try:
                    user: User = CurrentUserService.get_and_check_current_user()
                except Exception as err:
                    raise BadRequestException("An user is required") from err

            if isinstance(user, User):
                if not user.is_authenticated:
                    raise BadRequestException(
                        "An authenticated user is required")

                self.created_by = user
            else:
                raise BadRequestException(
                    "The user must be an instance of User")

            if not self.save():
                raise BadRequestException("Cannot create experiment")

            # attach the protocol
            protocol = kwargs.get("protocol")
            if protocol is None:
                from ..protocol.protocol import Protocol
                protocol = Protocol(user=user)

            protocol.set_experiment(self)
            self.protocol = protocol
            self.save()

        else:
            pass

        self._event_listener = EventListener()

    # -- A --

    def add_report(self, report: 'Report'):
        report.experiment = self

    def archive(self, archive: bool, archive_resources=True) -> bool:
        """
        Archive the experiment
        """

        if self.is_archived == archive:
            return True
        with self._db_manager.db.atomic() as transaction:
            Activity.add(
                Activity.ARCHIVE,
                object_type=self.full_classname(),
                object_uri=self.uri
            )
            if not self.protocol.archive(archive, archive_resources=archive_resources):
                transaction.rollback()
                return False
            status = super().archive(archive)
            if not status:
                transaction.rollback()
            return status

    # -- C --

    @classmethod
    def count_of_running_experiments(cls) -> int:
        """
        Returns the count of experiment in progress

        :return: The count of experiment in progress
        :rtype: `int`
        """

        return Experiment.select().where(Experiment._is_running).count()

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
    def is_finished(self) -> bool:
        if not self.id:
            return False

        e = Experiment.get_by_id(self.id)
        return e._is_finished

    @property
    def is_running(self) -> bool:
        if not self.id:
            return False

        experiment = Experiment.get_by_id(self.id)
        return experiment._is_running

    @property
    def is_draft(self) -> bool:
        """
        Returns True if the experiment is a draft, i.e. has nether been run and is not validated. False otherwise.

        :return: True if the experiment not running nor finished
        :rtype: `bool`
        """

        return (not self.is_validated) and (not self.is_running) and (not self.is_finished)

    @property
    def is_pid_alive(self) -> bool:
        if not self.pid:
            raise BadRequestException(f"No such process found")

        try:
            sproc = SysProc.from_pid(self.pid)
            return sproc.is_alive()
        except Exception as err:
            raise BadRequestException(
                f"No such process found or its access is denied (pid = {self.pid})") from err

    # -- J --

    # -- K --

    def kill_pid(self):
        """
        Kill the experiment through HTTP context if it is running

        This is only possible if the experiment has been started through the cli
        """

        if not HTTPHelper.is_http_context():
            raise BadRequestException("The user must be in http context")

        return self.kill_pid_through_cli()

    def kill_pid_through_cli(self):
        """
        Kill the experiment (through cli) if it is running

        This is only possible if the experiment has been started through the cli
        """

        if not self.pid:
            return

        try:
            sproc = SysProc.from_pid(self.pid)
        except Exception as err:
            raise BadRequestException(
                f"No such process found or its access is denied (pid = {self.pid}). Error: {err}") from err

        try:
            # Gracefully stops the experiment and exits!
            sproc.kill()
            sproc.wait()
        except Exception as err:
            raise BadRequestException(
                f"Cannot kill the experiment (pid = {self.pid}). Error: {err}") from err

        Activity.add(
            Activity.STOP,
            object_type=self.full_classname(),
            object_uri=self.uri
        )

        message = "Experiment manually stopped by a user."
        self.protocol.progress_bar.stop(message)
        self.data["pid"] = 0
        self._is_running = False
        self._is_finished = True
        self._is_success = False
        self.save()

    # -- O --

    def on_end(self, call_back: callable):
        self._event_listener.add("end", call_back)

    def on_start(self, call_back: callable):
        self._event_listener.add("start", call_back)

    # -- P --

    @property
    def pid(self) -> int:
        if not "pid" in self.data:
            return 0
        return self.data["pid"]

    @property
    def processes(self) -> List['Process']:
        """
        Returns child processes.
        """

        Q = []
        if self.id:
            from ..process.process import Process
            Qrel = Process.select().where(Process.experiment_id == self.id)
            for proc in Qrel:
                Q.append(proc.cast())
        return Q

    # -- R --

    @property
    def resources(self) -> List['Resource']:
        """
        Returns child resources.
        """

        Q = []
        if self.id:
            from ..resource.resource import ExperimentResource
            Qrel = ExperimentResource.select().where(
                ExperimentResource.experiment_id == self.id)
            for rel in Qrel:
                Q.append(rel.resource)  # is automatically casted
        return Q

    def reset(self) -> bool:
        """
        Reset the experiment.

        :return: True if it is reset, False otherwise
        :rtype: `bool`
        """

        if self.is_validated or self.is_running:
            return False

        if self.is_finished:
            with self._db_manager.db.atomic() as transaction:
                if self.protocol:
                    if not self.protocol._reset():
                        transaction.rollback()
                        return False

                self._is_running = False
                self._is_finished = False
                self._is_success = False
                self.score = None
                status = self.save()

                if not status:
                    transaction.rollback()

                return status
        else:
            return True

    async def mark_as_started(self):
        self.protocol.set_experiment(self)
        self.data["pid"] = 0
        self._is_running = True
        self._is_finished = False
        self.save()

        if self._event_listener.exists("start"):
            self._event_listener.sync_call("start", self)
            await self._event_listener.async_call("start", self)

    async def mark_as_success(self):
        if self._event_listener.exists("end"):
            self._event_listener.sync_call("end", self)
            await self._event_listener.async_call("end", self)

        self.data["pid"] = 0
        self._is_running = False
        self._is_finished = True
        self._is_success = True
        self.save()

    async def mark_as_error(self, error_message: str):
        self.protocol.progress_bar.stop(error_message)
        self.data["pid"] = 0
        self._is_running = False
        self._is_finished = True
        self._is_success = False
        self.save()
    # -- S --

    def set_title(self, title: str) -> str:
        """
        Set the title of the experiment. This title is set to the protocol.

        :param title: The title
        :type title: `str`
        """

        self.data["title"] = title

    def set_description(self, description: str) -> str:
        """
        Get the description of the experiment. This description is set to the protocol.

        :param description: The description
        :type description: `str`
        """

        self.data["description"] = description

    def save(self, *args, **kwargs):
        with self._db_manager.db.atomic() as transaction:
            if not self.is_saved():
                Activity.add(
                    Activity.CREATE,
                    object_type=self.full_classname(),
                    object_uri=self.uri
                )
            status = super().save(*args, **kwargs)
            if not status:
                transaction.rollback()
            return status

    # -- T --

    def to_json(self, *, stringify: bool = False, prettify: bool = False, **kwargs) -> Union[str, dict]:
        """
        Returns JSON string or dictionnary representation of the experiment.

        :param stringify: If True, returns a JSON string. Returns a python dictionary otherwise. Defaults to False
        :type stringify: bool
        :param prettify: If True, indent the JSON string. Defaults to False.
        :type prettify: bool
        :return: The representation
        :rtype: dict, str
        """

        _json = super().to_json(**kwargs)
        _json.update({
            "study": {"uri": self.study.uri},
            "protocol": {
                "uri": self.protocol.uri,
                "type": self.protocol.type
            },
            "is_draft": self.is_draft,
            "is_running": self.is_running,
            "is_finished": self.is_finished,
            "is_success": self._is_success
        })

        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json

    def validate(self, user: User) -> None:
        """
        Validate the experiment

        :param user: The user who validate the experiment
        :type user: `gws.user.User`
        """

        if self.is_validated:
            return
        if not self.is_finished:
            return
        with self._db_manager.db.atomic() as transaction:
            self.is_validated = True
            if self.save():
                Activity.add(
                    Activity.VALIDATE,
                    object_type=self.full_classname(),
                    object_uri=self.uri,
                    user=user
                )

    def check_user_privilege(self, user: User) -> None:
        return self.protocol.check_user_privilege(user)

    def check_is_runnable(self) -> None:
        """Throw an error if the experiment is not runnable
        """

        # check experiment status
        if self.is_archived:
            raise BadRequestException("The experiment is archived")
        if self.is_validated:
            raise BadRequestException("The experiment is validated")
        # if self.status == ExperimentStatus.RUNNING:
            # raise BadRequestException("The experiment is already running")

    def check_is_stopable(self) -> None:
        """Throw an error if the experiment is not stopable
        """

        # check experiment status
        if not self._is_running:
            raise BadRequestException(
                detail=f"Experiment '{self.uri}' is not running")
        elif self._is_finished:
            raise BadRequestException(
                detail=f"Experiment '{self.uri}' is already finished")

    # -- V --

# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from __future__ import annotations

from abc import abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Dict, Optional, Type, final

from peewee import CharField, ForeignKeyField

from gws_core.core.utils.date_helper import DateHelper
from gws_core.model.typing import Typing
from gws_core.task.plug import Source

from ..config.config import Config
from ..core.classes.enum_field import EnumField
from ..core.decorator.json_ignore import json_ignore
from ..core.decorator.transaction import transaction
from ..core.exception.exceptions import BadRequestException
from ..core.exception.exceptions.unauthorized_exception import \
    UnauthorizedException
from ..core.model.db_field import DateTimeUTC, JSONField
from ..core.model.model_with_user import ModelWithUser
from ..core.utils.logger import Logger
from ..experiment.experiment import Experiment
from ..io.io import Inputs, Outputs
from ..io.port import InPort, OutPort
from ..model.typing_manager import TypingManager
from ..progress_bar.progress_bar import ProgressBar, ProgressBarMessage
from ..user.user import User
from .process import Process
from .process_exception import ProcessRunException
from .process_types import ProcessErrorInfo

if TYPE_CHECKING:
    from ..protocol.protocol_model import ProtocolModel


class ProcessStatus(Enum):
    DRAFT = "DRAFT"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    # For protocol, it means that some process of protocol were not run (or added after run)
    PARTIALLY_RUN = "PARTIALLY_RUN"


@json_ignore(["parent_protocol_id"])
class ProcessModel(ModelWithUser):
    """Base abstract class for Process and Protocol

    :param Viewable: [description]
    :type Viewable: [type]
    """

    parent_protocol_id = CharField(max_length=36, null=True, index=True)
    experiment: Experiment = ForeignKeyField(
        Experiment, null=True, index=True, backref="+")
    instance_name = CharField(null=True)
    config: Config = ForeignKeyField(Config, null=False, backref='+')
    progress_bar: ProgressBar = ForeignKeyField(
        ProgressBar, null=True, backref='+')
    process_typing_name = CharField(null=False)
    brick_version = CharField(null=False, max_length=50, default="")
    status: ProcessStatus = EnumField(choices=ProcessStatus,
                                      default=ProcessStatus.DRAFT)
    error_info: ProcessErrorInfo = JSONField(null=True)

    started_at = DateTimeUTC(null=True)
    ended_at = DateTimeUTC(null=True)

    _experiment: Experiment = None
    _parent_protocol: ProtocolModel = None
    _inputs: Inputs = None
    _outputs: Outputs = None

    def __init__(self, *args, **kwargs):
        """
        Constructor
        """

        super().__init__(*args, **kwargs)

        self._inputs = None
        self._outputs = None

    ################################# MODEL METHODS #############################

    @transaction()
    def archive(self, archive: bool, archive_resources=True) -> ProcessModel:
        """
        Archive the process
        """

        if self.is_archived == archive:
            return self

        return super().archive(archive)

    @transaction()
    def delete_instance(self, *args, **kwargs):
        """Override delete instance to delete all the sub processes

        :return: [description]
        :rtype: [type]
        """

        result = super().delete_instance(*args, **kwargs)
        if self.config:
            self.config.delete_instance()
        if self.progress_bar:
            self.progress_bar.delete_instance()

        return result

    @property
    def parent_protocol(self) -> ProtocolModel:

        if not self._parent_protocol and self.parent_protocol_id:
            from ..protocol.protocol_model import ProtocolModel
            self._parent_protocol = ProtocolModel.get_by_id(
                self.parent_protocol_id)

        return self._parent_protocol

    @transaction()
    def reset(self) -> 'ProcessModel':
        """
        Reset the process
        """
        self.progress_bar.reset()

        self.status = ProcessStatus.DRAFT
        self.error_info = None
        self.started_at = None
        self.ended_at = None
        self._reset_io()
        process_model = self.save()
        return process_model

    @transaction()
    def reset_v2(self) -> 'ProcessModel':

        self.reset()

    def _reset_io(self):
        self.inputs.reset()
        self.outputs.reset()
        self.data["inputs"] = self.inputs.to_json()
        self.data["outputs"] = self.outputs.to_json()

    def save_after_task(self) -> None:
        """Method called after the task to save the process
        """
        self.save()

    def save_full(self) -> 'ProcessModel':
        """Function to run overrided by the sub classes
        """
        pass

    def set_parent_protocol(self, parent_protocol: ProtocolModel) -> None:
        """
        Sets the parent protocol of the process
        """

        from ..protocol.protocol_model import ProtocolModel
        if not isinstance(parent_protocol, ProtocolModel):
            raise BadRequestException(
                "An instance of ProtocolModel is required")
        if parent_protocol.id:
            self.parent_protocol_id = parent_protocol.id
        self._parent_protocol = parent_protocol

    def set_process_type(self, typing_name: str) -> None:
        typing: Typing = TypingManager.get_typing_from_name_and_check(
            typing_name)
        self.process_typing_name = typing_name
        self.brick_version = typing.brick_version

    def set_experiment(self, experiment: Experiment):
        if not isinstance(experiment, Experiment):
            raise BadRequestException("An instance of Experiment is required")

        if self.experiment and self.experiment.id != self.experiment.id:
            raise BadRequestException(
                "The protocol is already related to an experiment")
        self.experiment = experiment

    ################################# INPUTS #############################

    @property
    def inputs(self) -> Inputs:
        """
        Returns inputs of the process.

        :return: The inputs
        :rtype: Inputs
        """

        if self._inputs is None:
            self._init_inputs_from_data()
        return self._inputs

    def _init_inputs_from_data(self) -> None:
        """Init the inputs object from the inputs in the data
            Init the resource if they exists
        """
        if "inputs" not in self.data:
            self.data["inputs"] = {}

        self._inputs = Inputs.load_from_json(self.data["inputs"])

    def in_port(self, port_name: str) -> InPort:
        """
        Returns the port of the inputs by its name.

        :return: The port
        :rtype: InPort
        """
        return self.inputs.get_port(port_name)

    ################################# OUTPUTS #############################

    @property
    def outputs(self) -> Outputs:
        """
        Returns outputs of the process.

        :return: The outputs
        :rtype: Outputs
        """

        if self._outputs is None:
            self._init_outputs_from_data()
        return self._outputs

    def _init_outputs_from_data(self) -> None:
        """Init the ouput object from the outputs in the data
            Init the resource if they exists
        """
        if "outputs" not in self.data:
            self.data["outputs"] = {}

        self._outputs = Outputs.load_from_json(self.data["outputs"])

    def out_port(self, port_name: str) -> OutPort:
        """
        Returns the port of the outputs by its name.

        :return: The port
        :rtype: OutPort
        """
        return self.outputs.get_port(port_name)

    ################################# RUN #########################

    @final
    def run(self) -> None:
        """
        Run the process and save its state in the database.
        """

        try:
            self._run()
        # Catch all exception and wrap them into a ProcessRunException to provide process info
        except ProcessRunException as err:
            # if the process is already finished, just raise the exception
            if self.is_finished:
                raise err

            # When catching an error from a child process
            self.mark_as_error(
                {
                    "detail": err.get_detail_with_args(),
                    "unique_code": err.unique_code,
                    "context": err.context,
                    "instance_id": err.instance_id
                })

            # update the context to add this process
            err.update_context(self.get_instance_name_context())
            raise err
        except Exception as err:
            Logger.log_exception_stack_trace(err)
            # Create a new processRunException with correct info
            exception: ProcessRunException = ProcessRunException.from_exception(
                self, err)
            self.mark_as_error(
                {
                    "detail": exception.get_detail_with_args(),
                    "unique_code": exception.unique_code,
                    "context": None,
                    "instance_id": exception.instance_id
                })
            # update the context to add this process
            exception.update_context(self.get_instance_name_context())

            raise exception

    @abstractmethod
    def _run(self) -> None:
        """Function to run overrided by the sub classes
        """

    def _run_before_task(self) -> None:
        self.mark_as_started()

        # Set the data inputs dict
        self.data["inputs"] = self.inputs.to_json()

        self.save()

    def _run_after_task(self):
        self.mark_as_success()

        # Set the data outputs dict
        self.data["outputs"] = self.outputs.to_json()

        # Save the process (to save the new data)
        self.save_after_task()

    def check_user_privilege(self, user: User) -> None:
        """Throw an exception if the user cand execute the protocol

        :param user: user
        :type user: User
        """

        process_type: Type[Process] = self.get_process_type()

        if not user.has_access(process_type._allowed_user):
            raise UnauthorizedException(
                f"You must be a {process_type._allowed_user} to run the process '{process_type.full_classname()}'")

    def get_execution_time(self) -> float:
        """Return the execution time of the process

        :return: execution time in seconds
        :rtype: float
        """
        if self.progress_bar.started_at is None:
            return 0
        return (DateHelper.now_utc() - self.progress_bar.started_at).total_seconds() * 1000

    ########################### INFO #################################

    @abstractmethod
    def is_protocol(self) -> bool:
        pass

    def get_info(self) -> str:
        """Return basic information for this process (usefull for error message)
        """

        info: str = ""

        if self.instance_name:
            info += f"'{self.instance_name}' "

        return f"{info} ({self.get_process_type().classname()})"

    def get_instance_name_context(self) -> str:
        """ return the instance name in the context
        """

        # specific case for the main protocol (without parent)
        if self.parent_protocol_id is None:
            return "Main protocol"

        process_type: Type[Process] = TypingManager.get_type_from_name(
            self.process_typing_name)

        if process_type:
            return process_type._human_name

        return self.instance_name

    def get_name(self) -> str:
        """Return the name of the process
        """
        process_typing: Typing = self.get_process_typing()
        if process_typing:
            return process_typing.human_name

        return self.instance_name

    def get_process_type(self) -> Type[Process]:
        return TypingManager.get_type_from_name(self.process_typing_name)

    def get_process_typing(self) -> Typing:
        return TypingManager.get_typing_from_name(self.process_typing_name)

    def is_source_task(self) -> bool:
        """return true if the process is of type Source
        """
        return self.process_typing_name == Source._typing_name

    def get_last_message(self) -> Optional[ProgressBarMessage]:
        """Return the last message of the process
        """
        if self.progress_bar is None:
            return None

        return self.progress_bar.get_last_message()

    def get_progress_value(self) -> float:
        """Return the last message of the process
        """
        if self.progress_bar is None:
            return 0

        return self.progress_bar.current_value

    ########################### JSON #################################

    def get_minimum_json(self) -> dict:
        """
        Return the minium json to recognize this process

        """
        return {
            "id": self.id,
            "process_typing_name": self.process_typing_name,

        }

    def to_json(self, deep: bool = False, **kwargs) -> dict:
        """
        Returns JSON string or dictionnary representation of the process.

        :param stringify: If True, returns a JSON string. Returns a python dictionary otherwise. Defaults to False
        :type stringify: bool
        :param prettify: If True, indent the JSON string. Defaults to False.
        :type prettify: bool
        :return: The representation
        :rtype: dict, str
        """

        _json = super().to_json(deep=deep, **kwargs)

        _json["experiment_id"] = self.experiment.id if self.experiment else None
        _json["parent_protocol_id"] = self.parent_protocol.id if self.parent_protocol_id else None
        _json["is_running"] = self.progress_bar.is_running
        _json["is_finished"] = self.progress_bar.is_finished
        _json["is_protocol"] = self.is_protocol()

        _json["config"] = self.config.to_json(
            deep=deep, **kwargs)
        _json["progress_bar"] = self.progress_bar.to_json(deep=False)

        _json["inputs"] = self.inputs.to_json()
        _json["outputs"] = self.outputs.to_json()

        _json["typing_name"] = self._typing_name

        process_typing: Typing = self.get_process_typing()
        if process_typing:
            _json["human_name"] = process_typing.human_name
            _json["short_description"] = process_typing.short_description

        return _json

    def data_to_json(self, deep: bool = False, **kwargs) -> dict:
        """
        Returns a JSON string or dictionnary representation of the model.
        :return: The representation
        :rtype: `dict`
        """
        _json: dict = {}

        process_typing: Typing = self.get_process_typing()
        if process_typing:
            _json["title"] = process_typing.human_name
            _json["description"] = process_typing.short_description
            _json["doc"] = process_typing.get_model_type_doc()

        return _json

    def export_config(self) -> Dict:

        process_typing: Typing = self.get_process_typing()

        if process_typing is None:
            raise Exception(
                f"Could not find the process typing {self.process_typing_name}")

        return {
            "process_typing_name": self.process_typing_name,
            "instance_name": self.instance_name,
            "config": self.config.export_config(),
            "human_name": process_typing.human_name,
            "short_description": process_typing.short_description,
            "brick_version": self.brick_version,
            "inputs": self.inputs.to_json(),
            "outputs": self.outputs.to_json(),
            "status": self.status.value,
        }

    ########################### STATUS MANAGEMENT ##################################

    @property
    def is_running(self) -> bool:
        return self.status == ProcessStatus.RUNNING

    @property
    def is_runnable(self) -> bool:
        return (self.is_draft or self.is_partially_run) and self.inputs.is_ready

    @property
    def is_finished(self) -> bool:
        return self.is_success or self.is_error

    @property
    def is_draft(self) -> bool:
        return self.status == ProcessStatus.DRAFT

    def check_is_updatable(self) -> None:
        if self.is_running:
            raise BadRequestException(
                "The process is running and cannot be updated")
        if self.experiment:
            self.experiment.check_is_updatable()

    @property
    def is_error(self) -> bool:
        return self.status == ProcessStatus.ERROR

    @property
    def is_success(self) -> bool:
        return self.status == ProcessStatus.SUCCESS

    @property
    def is_partially_run(self) -> bool:
        return self.status == ProcessStatus.PARTIALLY_RUN

    @abstractmethod
    def mark_as_started(self):
        pass

    def mark_as_success(self):
        self.progress_bar.stop_success(
            f"End of process '{self.get_instance_name_context()}'",
            self.get_execution_time())
        self.status = ProcessStatus.SUCCESS
        self.ended_at = DateHelper.now_utc()
        self.save()

    def mark_as_error(self, error_info: ProcessErrorInfo):
        self.progress_bar.stop_error(error_info["detail"],
                                     self.get_execution_time())
        self.status = ProcessStatus.ERROR
        self.error_info = error_info
        self.ended_at = DateHelper.now_utc()
        self.save()

    def mark_as_error_and_parent(self, error_info: ProcessErrorInfo):
        self.progress_bar.stop_error(
            error_info["detail"], self.get_execution_time())
        self.status = ProcessStatus.ERROR
        self.error_info = error_info
        self.ended_at = DateHelper.now_utc()
        self.save()

        if self.parent_protocol and not self.parent_protocol.is_error:
            self.parent_protocol.mark_as_error_and_parent(error_info)


from __future__ import annotations

import asyncio
import inspect
from abc import abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, List, Type, Union, final

from peewee import CharField, ForeignKeyField, IntegerField
from starlette_context import context

from ..config.config import Config
from ..core.decorator.transaction import Transaction
from ..core.exception.exceptions import BadRequestException
from ..core.exception.exceptions.unauthorized_exception import \
    UnauthorizedException
from ..io.io import Input, Output
from ..io.port import InPort, OutPort
from ..model.typing_manager import TypingManager
from ..model.viewable import Viewable
from ..process.processable import Processable
from ..progress_bar.progress_bar import ProgressBar
from ..resource.processable_resource import ProcessableResource
from ..resource.resource_model import ResourceModel
from ..user.user import User
from .process_exception import ProcessableRunException

if TYPE_CHECKING:
    from ..experiment.experiment import Experiment
    from ..protocol.protocol_model import ProtocolModel


# Enum to define the role needed for a protocol
class ProcessAllowedUser(Enum):
    ADMIN = 0
    ALL = 1


class ProcessableModel(Viewable):
    """Base abstract class for Process and Protocol

    :param Viewable: [description]
    :type Viewable: [type]
    """

    # @ToDo:
    # ------
    # Try to replace `protocol_id` and `experiment_id` by foreign keys with `lazy_load=False`

    parent_protocol_id = IntegerField(null=True, index=True)
    experiment_id = IntegerField(null=True, index=True)
    instance_name = CharField(null=True, index=True)
    created_by = ForeignKeyField(User, null=False, index=True, backref='+')
    config = ForeignKeyField(Config, null=False, index=True, backref='+')
    progress_bar: ProgressBar = ForeignKeyField(
        ProgressBar, null=True, backref='+')
    processable_typing_name = CharField(null=False)

    is_instance_running = False
    is_instance_finished = False

    _experiment: Experiment = None
    _parent_protocol: ProtocolModel = None
    _input: Input = None
    _output: Output = None
    _is_singleton = False
    _is_removable = False

    # Role needed to run the protocol
    _allowed_user: ProcessAllowedUser = ProcessAllowedUser.ALL

    def __init__(self, *args, **kwargs):
        """
        Constructor
        """

        super().__init__(*args, **kwargs)

        self._input = Input(self)
        self._output = Output(self)

    # -- A --
    @Transaction()
    def archive(self, archive: bool, archive_resources=True) -> ProcessableModel:
        """
        Archive the process
        """

        if self.is_archived == archive:
            return self

        super().archive(archive)

        # -> try to archive the config if possible!
        self.config.archive(archive)
        if archive_resources:
            for resource in self.resources:
                resource.archive(archive)

        return self

    # -- D --

    def disconnect(self):
        """
        Disconnect the input and output ports
        """

        self.input.disconnect()
        self.output.disconnect()

    # -- E --
    # todo voir si on garde
    @property
    def experiment(self) -> Experiment:
        if not self._experiment and self.experiment_id:
            from ..experiment.experiment import Experiment
            self._experiment = Experiment.get_by_id(self.experiment_id)

        return self._experiment

    # -- G --

    def get_param(self, name: str) -> Union[str, int, float, bool, list, dict]:
        """
        Returns the value of a parameter of the process config by its name.

        :return: The paremter value
        :rtype: [str, int, float, bool]
        """

        return self.config.get_param(name)

    def get_next_procs(self) -> list:
        """
        Returns the list of (right-hand side) processes connected to the IO ports.

        :return: List of processes
        :rtype: list
        """

        return self.output.get_next_procs()

    # -- H --

    # -- I --

    @property
    def is_running(self) -> bool:
        if not self.progress_bar:
            return False
        progress_bar: ProgressBar = ProgressBar.get_by_id(self.progress_bar.id)
        return progress_bar.is_running

    @property
    def is_finished(self) -> bool:
        if not self.progress_bar:
            return False
        progress_bar: ProgressBar = ProgressBar.get_by_id(self.progress_bar.id)
        return progress_bar.is_finished

    @property
    def is_ready(self) -> bool:
        """
        Returns True if the process is ready (i.e. all its ports are
        ready or it has never been run before), False otherwise.

        :return: True if the process is ready, False otherwise.
        :rtype: bool
        """

        return (not self.is_instance_running and not self.is_instance_finished) and self.input.is_ready

    @property
    def input(self) -> Input:
        """
        Returns input of the process.

        :return: The input
        :rtype: Input
        """

        if self._input.is_empty:
            self._init_input()
        return self._input

    def _init_input(self) -> None:
        if not "input" in self.data:
            return
        for key in self.data["input"]:
            resource: ResourceModel = TypingManager.get_object_with_typing_name_and_uri(
                self.data["input"][key]["typing_name"], self.data["input"][key]["uri"])
            self._input.set_item_without_check(key, resource)

    def in_port(self, name: str) -> InPort:
        """
        Returns the port of the input by its name.

        :return: The port
        :rtype: InPort
        """

        if not isinstance(name, str):
            raise BadRequestException(
                "The name of the input port must be a string")
        if not self.input.port_exists(name):
            raise BadRequestException(f"The input port '{name}' is not found")
        return self.input._ports[name]

    # -- J --

    # -- L --

    def __lshift__(self, name: str) -> InPort:
        """
        Alias of :meth:`in_port`.
        Returns the port of the input by its name

        :return: The port
        :rtype: InPort
        """

        return self.in_port(name)

    # -- O --

    @property
    def output(self) -> Output:
        """
        Returns output of the process.

        :return: The output
        :rtype: Output
        """

        if self._output.is_empty:
            self._init_output()
        return self._output

    def _init_output(self) -> None:
        if not "output" in self.data:
            return

        for key in self.data["output"]:
            resource: ResourceModel = TypingManager.get_object_with_typing_name_and_uri(
                self.data["output"][key]["typing_name"], self.data["output"][key]["uri"])
            self._output.set_item_without_check(key, resource)

    def out_port(self, name: str) -> OutPort:
        """
        Returns the port of the output by its name.

        :return: The port
        :rtype: OutPort
        """
        if not isinstance(name, str):
            raise BadRequestException(
                "The name of the output port must be a string")
        if not self.output.port_exists(name):
            raise BadRequestException(f"The output port '{name}' is not found")
        return self.output._ports[name]

    @property
    def parent_protocol(self) -> ProtocolModel:

        if not self._parent_protocol and self.parent_protocol_id:
            from ..protocol.protocol_model import ProtocolModel
            self._parent_protocol = ProtocolModel.get_by_id(self.parent_protocol_id)

        return self._parent_protocol

    # -- R --

    @property
    def resources(self) -> List[ResourceModel]:
        Qrel: List[ProcessableResource] = ProcessableResource.select().where(ProcessableResource.process_id == self.id)
        Q = []
        for o in Qrel:
            Q.append(o.resource)
        return Q

    @Transaction()
    def reset(self) -> 'ProcessableModel':
        """
        Reset the process

        :return: Returns True if is process is successfully reset;  False otherwise
        :rtype: `bool`
        """

        if self.is_running:
            return None
        self.progress_bar.reset()
        self._reset_io()
        return self.save()

    def _reset_io(self):
        self.input.reset()
        self.output.reset()
        self.data["input"] = {}
        self.data["output"] = {}

    @final
    async def run(self) -> None:
        """
        Run the process and save its state in the database.
        """

        if not self.is_ready:
            return

        try:
            await self._run()
        # Catch all exception and wrap them into a ProcessRunException to provide processable info
        except Exception as err:
            raise ProcessableRunException.from_exception(self, err)

    @abstractmethod
    async def _run(self) -> None:
        """Function to run overrided by the sub classes
        """
        pass

    async def _run_next_processes(self):
        self.output.propagate()
        aws = []
        for proc in self.output.get_next_procs():
            aws.append(proc.run())
        if len(aws):
            await asyncio.gather(*aws)

    async def _run_before_task(self):
        self.__switch_to_current_progress_bar()
        ProgressBar.add_message_to_current(
            f"Running {self.full_classname()} ...")
        self.is_instance_running = True
        self.is_instance_finished = False
        self.data["input"] = {}
        for k in self.input:
            # -> check that an input resource exists (for optional input)
            if self.input[k]:
                if not self.input[k].is_saved():
                    self.input[k].save()
                self.data["input"][k] = {
                    "uri": self.input[k].uri,
                    "typing_name": self.input[k].typing_name
                }
        self.progress_bar.start()
        self.save()

    async def _run_after_task(self):
        ProgressBar.add_message_to_current(
            f"Task of {self.full_classname()} successfully finished!")
        self.is_instance_running = False
        self.is_instance_finished = True
        self.progress_bar.stop()

        if not self.output.is_ready:
            return

        self.data["output"] = {}
        for k in self.output:
            # -> check that an output resource exists (for optional outputs)
            if self.output[k]:
                self.data["output"][k] = {
                    "uri": self.output[k].uri,
                    "typing_name": self.output[k].typing_name
                }
        await self._run_next_processes()

    def __rshift__(self, name: str) -> OutPort:
        """
        Alias of :meth:`out_port`.

        Returns the port of the output by its name
        :return: The port
        :rtype: OutPort
        """

        return self.out_port(name)

    # -- S --

    def save_full(self) -> 'ProcessableModel':
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

    def __switch_to_current_progress_bar(self):
        """
        Swicth to the application to current progress bar.

        The current progress bar will be accessible everywhere (i.e. at the application level)
        """

        try:
            context.data["progress_bar"] = self.progress_bar
        except:
            pass

    def set_experiment(self, experiment: Experiment):
        from ..experiment.experiment import Experiment
        if not isinstance(experiment, Experiment):
            raise BadRequestException("An instance of Experiment is required")
        if not experiment.id:
            if not experiment.save():
                raise BadRequestException("Cannot save the experiment")
        if self.experiment_id and self.experiment_id != experiment.id:
            raise BadRequestException(
                "The protocol is already related to an experiment")
        self.experiment_id = experiment.id
        self.save()

    def set_input(self, name: str, resource: 'ResourceModel'):
        """
        Sets the resource of an input port by its name.

        :param name: The name of the input port
        :type name: str
        :param resource: A reources to assign to the port
        :type resource: ResourceModel
        """

        if not isinstance(name, str):
            raise BadRequestException("The name must be a string.")

        # if not not isinstance(resource, ResourceModel):
        #    raise BadRequestException("The resource must be an instance of ResourceModel.")

        self._input[name] = resource

    def set_config(self, config: Config):
        """
        Sets the config of the process.

        :param config: A config to assign
        :type config: Config
        """

        self.config = config
        self.save()

    def set_param(self, name: str, value: Union[str, int, float, bool]):
        """
        Sets the value of a config parameter.

        :param name: Name of the parameter
        :type name: str
        :param value: A value to assign
        :type value: [str, int, float, bool]
        """

        self.config.set_param(name, value)
        self.config.save()

    # -- T --

    def _get_processable_type(self) -> Type[Processable]:
        return TypingManager.get_type_from_name(self.processable_typing_name)

    @final
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

        del _json["experiment_id"]
        del _json["parent_protocol_id"]
        if "input" in _json["data"]:
            del _json["data"]["input"]
        if "output" in _json["data"]:
            del _json["data"]["output"]

        _json["experiment"] = {
            "uri": (self.experiment.uri if self.experiment_id else "")}
        _json["protocol"] = {
            "uri": (self.parent_protocol.uri if self.parent_protocol_id else "")}
        _json["is_running"] = self.progress_bar.is_running
        _json["is_finished"] = self.progress_bar.is_finished

        if not deep:
            _json["config"] = {"uri": self.config.uri}
            _json["progress_bar"] = {"uri": self.progress_bar.uri}
            # if _json["data"].get("graph"):
            #    del _json["data"]["graph"]
        else:
            _json["config"] = self.config.to_json(
                deep=deep, **kwargs)
            _json["progress_bar"] = self.progress_bar.to_json(
                deep=deep, **kwargs)

        _json["input"] = self.input.to_json(
            deep=deep, **kwargs)
        _json["output"] = self.output.to_json(
            deep=deep, **kwargs)

        return _json

    def data_to_json(self, deep: bool = False, **kwargs) -> dict:
        """
        Returns a JSON string or dictionnary representation of the model.
        :return: The representation
        :rtype: `dict`
        """
        _json = super().data_to_json(deep=deep, **kwargs)

        processable_type: Type[Processable] = TypingManager.get_type_from_name(
            self.processable_typing_name)
        _json["title"] = processable_type._human_name
        _json["description"] = processable_type._short_description
        _json["doc"] = inspect.getdoc(processable_type)

        return _json

    def check_user_privilege(self, user: User) -> None:
        """Throw an exception if the user cand execute the protocol

        :param user: user
        :type user: User
        """

        process_type: Type[Processable] = self._get_processable_type()

        if not user.has_access(process_type._allowed_user):
            raise UnauthorizedException(
                f"You must be a {process_type._allowed_user} to run the process '{process_type.full_classname()}'")

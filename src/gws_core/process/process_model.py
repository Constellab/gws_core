

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Optional, Type, final

from peewee import BooleanField, CharField, ForeignKeyField

from gws_core.config.config_types import ConfigParamsDict
from gws_core.core.exception.gws_exceptions import GWSException
from gws_core.core.utils.date_helper import DateHelper
from gws_core.io.io_dto import IODTO
from gws_core.io.io_specs import IOSpecs
from gws_core.model.typing import Typing
from gws_core.model.typing_dto import SimpleTypingDTO, TypingStatus
from gws_core.model.typing_style import TypingStyle
from gws_core.process.process_dto import ProcessDTO
from gws_core.progress_bar.progress_bar_dto import ProgressBarMessageDTO
from gws_core.protocol.protocol_dto import ProcessConfigDTO
from gws_core.task.plug import Sink, Source

from ..config.config import Config
from ..core.classes.enum_field import EnumField
from ..core.decorator.transaction import transaction
from ..core.exception.exceptions import BadRequestException
from ..core.model.db_field import BaseDTOField, DateTimeUTC, JSONField
from ..core.model.model_with_user import ModelWithUser
from ..core.utils.logger import Logger
from ..experiment.experiment import Experiment
from ..io.io import Inputs, Outputs
from ..io.port import InPort, OutPort
from ..model.typing_manager import TypingManager
from ..progress_bar.progress_bar import ProgressBar
from .process import Process
from .process_exception import ProcessRunException
from .process_types import ProcessErrorInfo, ProcessMinimumDTO, ProcessStatus

if TYPE_CHECKING:
    from ..protocol.protocol_model import ProtocolModel


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
    # version of the brick when the process was created
    brick_version_on_create = CharField(null=False, max_length=50, default="")
    # version of the brick when the process was run
    brick_version_on_run = CharField(null=True, max_length=50, default="")
    status: ProcessStatus = EnumField(choices=ProcessStatus,
                                      default=ProcessStatus.DRAFT)
    error_info: ProcessErrorInfo = JSONField(null=True)

    started_at = DateTimeUTC(null=True)
    ended_at = DateTimeUTC(null=True)

    data: Dict[str, Any] = JSONField(null=True)
    is_archived = BooleanField(default=False, index=True)
    style: TypingStyle = BaseDTOField(TypingStyle, null=True)

    # name of the process set by the user
    name = CharField(null=True)

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

        if not self.is_saved() and not self.data:
            self.data = {}

    ################################# MODEL METHODS #############################

    @transaction()
    def archive(self, archive: bool) -> ProcessModel:
        """
        Archive the process
        """

        if self.is_archived == archive:
            return self

        self.is_archived = archive
        return self.save()

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
        self.set_error_info(None)
        self.started_at = None
        self.ended_at = None
        self._reset_io()
        process_model = self.save()
        return process_model

    def _reset_io(self):
        self.inputs.reset()
        self.outputs.reset()
        self.data["inputs"] = self.inputs.to_json()
        self.data["outputs"] = self.outputs.to_json()

    def save(self, *args, **kwargs) -> 'ProcessModel':
        """Override save to save the inputs and outputs
        """

        # if inputs were loaded, save them
        if self._inputs:
            self.data["inputs"] = self.inputs.to_json()

        # if outputs were loaded, save them
        if self._outputs:
            self.data["outputs"] = self.outputs.to_json()
        return super().save(*args, **kwargs)

    def save_full(self) -> 'ProcessModel':
        """Function to run overrided by the sub classes
        """
        pass

    def set_parent_protocol(self, parent_protocol: ProtocolModel) -> None:
        """
        Sets the parent protocol of the process
        """

        if parent_protocol.id:
            self.parent_protocol_id = parent_protocol.id
        self._parent_protocol = parent_protocol

        self.set_experiment(parent_protocol.experiment)

    def set_process_type(self, process_type: Type[Process]) -> None:
        self.process_typing_name = process_type.get_typing_name()
        self.brick_version_on_create = self._get_type_brick_version()
        self.name = process_type.get_human_name()

    def set_inputs_from_specs(self, inputs_specs: IOSpecs) -> None:
        """Set the inputs from specs
        """
        self._inputs = Inputs.load_from_specs(inputs_specs)

        # Set the data inputs dict
        self.data["inputs"] = self.inputs.to_json()

    def set_outputs_from_specs(self, outputs_specs: IOSpecs) -> None:
        """Set the outputs from specs
        """
        self._outputs = Outputs.load_from_specs(outputs_specs)
        # Set the data inputs dict
        self.data["outputs"] = self.outputs.to_json()

    def set_inputs_from_dto(self, inputs_dto: IODTO, reset: bool = False) -> None:
        """Set the inputs from a DTO
        """
        self._inputs = Inputs.load_from_dto(inputs_dto)

        if reset:
            self._inputs.reset()
        # Set the data inputs dict
        self.data["inputs"] = self.inputs.to_json()

    def set_outputs_from_dto(self, outputs_dto: IODTO, reset: bool = False) -> None:
        """Set the outputs from a DTO
        """
        self._outputs = Outputs.load_from_dto(outputs_dto)
        if reset:
            self._outputs.reset()
        # Set the data inputs dict
        self.data["outputs"] = self.outputs.to_json()

    def _get_type_brick_version(self) -> str:
        typing: Typing = TypingManager.get_typing_from_name_and_check(self.process_typing_name)
        return typing.brick_version

    def set_experiment(self, experiment: Experiment) -> None:
        self.experiment = experiment

    def get_error_info(self) -> Optional[ProcessErrorInfo]:
        return ProcessErrorInfo.from_json(self.error_info) if self.error_info else None

    def set_error_info(self, error_info: ProcessErrorInfo) -> None:
        self.error_info = error_info.to_json_dict() if error_info else None

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
            self.mark_as_error_and_parent(err)
            raise err
        except Exception as err:
            Logger.log_exception_stack_trace(err)
            # Create a new processRunException with correct info
            exception: ProcessRunException = ProcessRunException.from_exception(
                self, err)
            self.mark_as_error_and_parent(exception)
            raise exception

    @abstractmethod
    def _run(self) -> None:
        """Function to run overrided by the sub classes
        """

    def _run_before_task(self) -> None:
        self.mark_as_started()

        # Set the data inputs dict
        self.data["inputs"] = self.inputs.to_json()

        # save the version of the brick when the process was run
        self.brick_version_on_run = self._get_type_brick_version()

        self.save()

    def _run_after_task(self):
        # Set the data outputs dict
        self.data["outputs"] = self.outputs.to_json()

    def get_execution_time(self) -> float:
        """Return the execution time of the process

        :return: execution time in seconds
        :rtype: float
        """
        if self.progress_bar.started_at is None:
            return 0
        return (DateHelper.now_utc() - self.progress_bar.started_at).total_seconds() * 1000

    ########################### CONFIG #################################

    def set_config_value(self, param_name: str, value: Any) -> None:
        """Set a value of the config

        :param param_name: [description]
        :type param_name: str
        :param value: [description]
        :type value: Any
        """

        self.config.set_value(param_name, value)

    def set_config_values(self, config_values: ConfigParamsDict) -> None:
        """Set the config values

        :param config_values: [description]
        :type config_values: Dict[str, Any]
        """

        self.config.set_values(config_values)

    def set_config(self, config: Config) -> None:
        """Set the config object

        :param config: [description]
        :type config: ConfigParamsDict
        """
        self.config = config

    ########################### INFO #################################

    @abstractmethod
    def is_protocol(self) -> bool:
        pass

    def get_instance_name_context(self) -> str:
        """ return the instance name in the context
        """

        # specific case for the main protocol (without parent)
        if self.parent_protocol_id is None:
            return "Main protocol"

        return self.get_name()

    def get_instance_path(self) -> str:
        """Return the instance path
        """
        if self.parent_protocol_id:
            parent_path = self.parent_protocol.get_instance_path()
            if len(parent_path) > 0:
                return f"{parent_path}.{self.get_instance_name_context()}"
            else:
                return self.instance_name
        return ""

    def get_name(self) -> str:
        """Return the name of the process
        """
        return self.name

    def get_process_type(self) -> Type[Process]:
        return TypingManager.get_and_check_type_from_name(self.process_typing_name)

    def get_process_typing(self) -> Typing:
        return TypingManager.get_typing_from_name(self.process_typing_name)

    def is_source_task(self) -> bool:
        """return true if the process is of type Source
        """
        return self.process_typing_name == Source.get_typing_name()

    def is_sink_task(self) -> bool:
        """return true if the process is of type Sink
        """
        return self.process_typing_name == Sink.get_typing_name()

    def is_auto_run(self) -> bool:
        """Return true if the process is of type Source
        """
        return self.get_process_type().__auto_run__

    def is_enable_in_sub_protocol(self) -> bool:
        """Return true if the process is enable in sub protocol
        """
        return self.get_process_type().__enable_in_sub_protocol__

    def get_last_message(self) -> Optional[ProgressBarMessageDTO]:
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

    def to_minimum_dto(self) -> ProcessMinimumDTO:
        """
        Return the minium json to recognize this process

        """
        return ProcessMinimumDTO(
            id=self.id,
            process_typing_name=self.process_typing_name,
        )

    def to_dto(self) -> ProcessDTO:

        process_typing: Typing = self.get_process_typing()
        process_type_dto: SimpleTypingDTO = None
        type_status: TypingStatus = TypingStatus.OK
        style: TypingStyle = self.style

        if process_typing:
            process_type_dto = process_typing.to_simple_dto()
            type_status = process_typing.get_type_status()
            if style is None:
                style = process_typing.style
        else:
            type_status = TypingStatus.UNAVAILABLE

        if style is None:
            style = TypingStyle.default_task()

        return ProcessDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            created_by=self.created_by.to_dto(),
            last_modified_by=self.last_modified_by.to_dto(),
            parent_protocol_id=self.parent_protocol.id if self.parent_protocol_id else None,
            experiment_id=self.experiment.id if self.experiment else None,
            instance_name=self.instance_name,
            config=self.config.to_dto(),
            progress_bar=self.progress_bar.to_dto(),
            process_typing_name=self.process_typing_name,
            brick_version_on_create=self.brick_version_on_create,
            brick_version_on_run=self.brick_version_on_run,
            status=self.status,
            error_info=self.get_error_info(),
            started_at=self.started_at,
            ended_at=self.ended_at,
            is_archived=self.is_archived,
            is_protocol=self.is_protocol(),
            inputs=self.inputs.to_dto(),
            outputs=self.outputs.to_dto(),
            type_status=type_status,
            process_type=process_type_dto,
            name=self.name,
            style=style
        )

    def to_config_dto(self, ignore_source_config: bool = False) -> ProcessConfigDTO:
        """Return the config DTO

        :param ignore_source_config: if true, the config values of Source task is ignored, defaults to False
        :type ignore_source_config: bool, optional
        :return: _description_
        :rtype: ProcessConfigDTO
        """

        process_typing: Typing = self.get_process_typing()

        if process_typing is None:
            raise Exception(
                f"Could not find the process typing {self.process_typing_name}")

        ignore_config_values = ignore_source_config and self.is_source_task()

        return ProcessConfigDTO(
            process_typing_name=self.process_typing_name,
            instance_name=self.instance_name,
            config=self.config.to_simple_dto(ignore_config_values),
            name=self.name,
            brick_version_on_create=self.brick_version_on_create,
            brick_version_on_run=self.brick_version_on_run,
            inputs=self.inputs.to_dto(),
            outputs=self.outputs.to_dto(),
            status=self.status.value,
            process_type=process_typing.to_simple_dto(),
            style=self.style or process_typing.style,
            progress_bar=self.progress_bar.to_config_dto(),
        )

    ########################### STATUS MANAGEMENT ##################################

    @property
    def is_running(self) -> bool:
        return self.status == ProcessStatus.RUNNING

    @property
    def is_runnable(self) -> bool:
        return (self.is_draft or self.is_partially_run or
                self.status == ProcessStatus.WAITING_FOR_CLI_PROCESS) and self.inputs.is_ready

    @property
    def is_finished(self) -> bool:
        return self.is_success or self.is_error

    @property
    def is_draft(self) -> bool:
        return self.status == ProcessStatus.DRAFT

    def check_is_updatable(self, error_if_finished: bool = True) -> None:
        if self.is_running:
            raise BadRequestException(GWSException.PROCESS_UPDATE_RUNNING_ERROR.value,
                                      GWSException.PROCESS_UPDATE_RUNNING_ERROR.name)

        if error_if_finished and self.is_finished and not self.is_auto_run():
            raise BadRequestException(GWSException.PROCESS_UPDATE_FISHINED_ERROR.value,
                                      GWSException.PROCESS_UPDATE_FISHINED_ERROR.name)

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
        if self.is_success:
            return
        self.progress_bar.stop_success(
            f"End of process '{self.get_instance_name_context()}'",
            self.get_execution_time())
        self.status = ProcessStatus.SUCCESS
        self.ended_at = DateHelper.now_utc()
        self.save()

    def mark_as_error(self, error_info: ProcessErrorInfo):
        if self.is_error:
            return
        self.progress_bar.stop_error(error_info.detail,
                                     self.get_execution_time())
        self.status = ProcessStatus.ERROR
        self.set_error_info(error_info)
        self.ended_at = DateHelper.now_utc()
        self.save()

    def mark_as_error_and_parent(self, process_error: ProcessRunException, context: str = None):
        self.mark_as_error(ProcessErrorInfo(
            detail=process_error.get_error_message(context),
            unique_code=process_error.unique_code,
            context=context,
            instance_id=process_error.instance_id
        ))

        new_context: str = f"{self.get_instance_name_context()}"
        if context:
            new_context += f" > {context}"

        if self.parent_protocol:
            self.parent_protocol.mark_as_error_and_parent(process_error, new_context)
        # once we reach the main protocol, we mark the experiment as error
        elif self.experiment:
            self.experiment.mark_as_error(ProcessErrorInfo(
                detail=process_error.get_error_message(new_context),
                unique_code=process_error.unique_code,
                context=new_context,
                instance_id=process_error.instance_id
            ))

    def mark_as_waiting_for_cli_process(self):
        self.status = ProcessStatus.WAITING_FOR_CLI_PROCESS
        self.save()

    def is_root_process(self) -> bool:
        return self.parent_protocol_id is None

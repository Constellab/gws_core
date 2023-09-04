# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from abc import abstractmethod
from typing import Optional, Type

from gws_core.model.typing import Typing
from gws_core.process.process_types import (ProcessConfigDict,
                                            ProcessMinimumDict)
from gws_core.protocol.protocol import Protocol
from gws_core.task.task import Task

from ..config.config_types import ConfigParamsDict
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..model.typing_manager import TypingManager
from ..task.task_model import TaskModel
from .process import Process
from .process_model import ProcessModel


class ProtocolSubProcessBuilder():
    """Builder used by the ProtocolModel build method to instantiate processs of Protocol form the node json Dict
    """

    @abstractmethod
    def instantiate_process_from_json(self, node_json: dict, instance_name: str) -> ProcessModel:
        pass


class SubProcessBuilderReadFromDb(ProtocolSubProcessBuilder):
    """Factory used when getting a protocol from the database,  it read the protocol's processes
    from the DB
    """

    def instantiate_process_from_json(self, node_json: ProcessMinimumDict, instance_name: str) -> ProcessModel:
        proc_id: str = node_json.get("id", None)

        proc_type_str: str = node_json["process_typing_name"]
        is_protocol = Typing.typing_name_is_protocol(proc_type_str)

        return self._get_process_from_db(process_id=proc_id, is_protocol=is_protocol)

    def _get_process_from_db(self, process_id: Optional[str],
                             is_protocol: bool) -> ProcessModel:
        """Method to retrieve the process from the DB
        """
        # Instantiate a process
        if is_protocol:
            from ..protocol.protocol_model import ProtocolModel
            return ProtocolModel.get_by_id_and_check(process_id)
        else:
            return TaskModel.get_by_id_and_check(process_id)


class SubProcessBuilderCreate(ProtocolSubProcessBuilder):
    """Factory used to force creation of a processes when building a protocol
    It requires a ProcessConfigDict instead of a ProcessMinimumDict
    """

    def instantiate_process_from_json(self, node_json: ProcessConfigDict, instance_name: str) -> ProcessModel:
        process_type_str: str = node_json["process_typing_name"]
        process_type: Type[Process] = TypingManager.get_type_from_name(process_type_str)

        if process_type is None:
            raise BadRequestException(
                f"Process {process_type_str} is not defined. Please ensure that the corresponding brick is loaded.")

        return self._create_new_process(process_type=process_type, instance_name=instance_name,
                                        node_json=node_json)

    def _create_new_process(self, process_type: Type[Process],
                            instance_name: str, node_json: ProcessConfigDict) -> ProcessModel:
        """Method to instantiate a new process and configure it
        """
        from ..process.process_factory import ProcessFactory

        config_params: ConfigParamsDict = {}
        # Configure the process
        if node_json.get('config'):
            config_params = node_json.get('config').get("values", {})

        if issubclass(process_type, Task):
            return ProcessFactory.create_task_model_from_type(process_type, config_params, instance_name,
                                                              node_json.get('inputs'),
                                                              node_json.get('outputs'))
        elif issubclass(process_type, Protocol):
            return ProcessFactory.create_protocol_model_from_type(process_type, config_params, instance_name)
        else:
            name = process_type.__name__ if process_type.__name__ is not None else str(
                process_type)
            raise BadRequestException(
                f"The type {name} is not a Process nor a Protocol. It must extend the on of the classes")

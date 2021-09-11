# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from abc import abstractmethod
from typing import Dict, Optional, Type

from pydantic.types import NoneBytes

from ..config.config_types import ConfigParamsDict
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..model.typing_manager import TypingManager
from ..task.task import Task
from ..task.task_model import TaskModel
from .process import Process
from .process_model import ProcessModel


class ProtocolSubProcessBuilder():
    """Builder used by the ProtocolModel build method to instantiate processs of Protocol form the node json Dict
    """

    def instantiate_process_from_json(self, node_json: Dict, instance_name: str) -> ProcessModel:
        proc_uri: str = node_json.get("uri", None)

        proc_type_str: str = node_json["process_typing_name"]
        proc_type: Type[Process] = TypingManager.get_type_from_name(proc_type_str)

        if proc_type is None:
            raise BadRequestException(
                f"Process {proc_type_str} is not defined. Please ensure that the corresponding brick is loaded.")

        # create the process instance
        return self._instantiate_process(process_uri=proc_uri,
                                         process_type=proc_type,
                                         instance_name=instance_name,
                                         node_json=node_json)

    @abstractmethod
    def _instantiate_process(self, process_uri: Optional[str],
                             process_type: Type[Process],
                             instance_name: str,
                             node_json: Dict) -> ProcessModel:
        """Overriden by the children
        """
        pass

    def _get_process_from_db(self, process_uri: Optional[str],
                             process_type: Type[Process]) -> ProcessModel:
        """Method to retrieve the process from the DB
        """
        # Instantiate a process
        if issubclass(process_type, Task):
            return TaskModel.get_by_uri_and_check(process_uri)
        else:
            from ..protocol.protocol_model import ProtocolModel
            return ProtocolModel.get_by_uri_and_check(process_uri)

    def _create_new_process(self, process_type: Type[Process],
                            instance_name: str, node_json: Dict) -> ProcessModel:
        """Method to instantiate a new process and configure it
        """
        from ..process.process_factory import ProcessFactory

        config_values: ConfigParamsDict = NoneBytes
        # Configure the process
        if node_json.get('config'):
            config_values = node_json.get('config').get("data", {}).get("values", {})

        return ProcessFactory.create_process_model_from_type(
            process_type=process_type, config_values=config_values, instance_name=instance_name)


class SubProcessBuilderReadFromDb(ProtocolSubProcessBuilder):
    """Factory used when getting a protocol from the database,  it read the protocol's processes
    from the DB
    """

    def _instantiate_process(self, process_uri: Optional[str],
                             process_type: Type[Process],
                             instance_name: str,
                             node_json: Dict) -> ProcessModel:
        if process_uri is None:
            raise BadRequestException(
                f"Cannot instantiate the process {instance_name} because it does not have an uri")

        return self._get_process_from_db(process_uri=process_uri, process_type=process_type)


class SubProcessBuilderCreate(ProtocolSubProcessBuilder):
    """Factory used to force creation of a processes when building a protocol
    """

    def _instantiate_process(self, process_uri: Optional[str],
                             process_type: Type[Process],
                             instance_name: str,
                             node_json: Dict) -> ProcessModel:

        return self._create_new_process(process_type=process_type, instance_name=instance_name,
                                        node_json=node_json)


class SubProcessBuilderUpdate(ProtocolSubProcessBuilder):
    """Factory used to get the processes or create a new one when building a protocol
    """

    def _instantiate_process(self, process_uri: Optional[str],
                             process_type: Type[Process],
                             instance_name: str,
                             node_json: Dict) -> ProcessModel:

        if process_uri is not None:
            process_model: ProcessModel = self._get_process_from_db(
                process_uri=process_uri, process_type=process_type)

            # Update the process config
            if node_json.get('config'):
                params = node_json.get('config').get("data", {}).get("values", {})
                process_model.config.set_values(params)

            return process_model

        else:
            return self._create_new_process(process_type=process_type, instance_name=instance_name,
                                            node_json=node_json)



from abc import abstractmethod
from typing import Dict, Optional, Type

from pydantic.types import NoneBytes

from ..config.config_spec import ConfigValues
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..model.typing_manager import TypingManager
from ..process.process import Process
from ..process.process_model import ProcessModel
from .processable import Processable
from .processable_model import ProcessableModel


class SubProcessableFactory():
    """Factory used by the ProtocolModel builder to instantiate processs of Protocol form the node json Dict
    """

    def instantiate_processable_from_json(self, node_json: Dict, instance_name: str) -> ProcessableModel:
        proc_uri: str = node_json.get("uri", None)

        proc_type_str: str = node_json["processable_typing_name"]
        proc_type: Type[Processable] = TypingManager.get_type_from_name(proc_type_str)

        if proc_type is None:
            raise BadRequestException(
                f"Process {proc_type_str} is not defined. Please ensure that the corresponding brick is loaded.")

        # create the processable instance
        return self._instantiate_processable(processable_uri=proc_uri,
                                             processable_type=proc_type,
                                             instance_name=instance_name,
                                             node_json=node_json)

    @abstractmethod
    def _instantiate_processable(self, processable_uri: Optional[str],
                                 processable_type: Type[Processable],
                                 instance_name: str,
                                 node_json: Dict) -> ProcessableModel:
        """Overriden by the children
        """
        pass

    def _get_processable_from_db(self, processable_uri: Optional[str],
                                 processable_type: Type[Processable]) -> ProcessableModel:
        """Method to retrieve the processable from the DB
        """
        # Instantiate a process
        if issubclass(processable_type, Process):
            return ProcessModel.get_by_uri_and_check(processable_uri)
        else:
            from ..protocol.protocol_model import ProtocolModel
            return ProtocolModel.get_by_uri_and_check(processable_uri)

    def _create_new_processable(self, processable_type: Type[Processable],
                                instance_name: str, node_json: Dict) -> ProcessableModel:
        """Method to instantiate a new processable and configure it
        """
        from ..processable.processable_factory import ProcessableFactory

        config_values: ConfigValues = NoneBytes
        # Configure the process
        if node_json.get('config'):
            config_values = node_json.get('config').get("data", {}).get("params", {})

        return ProcessableFactory.create_processable_model_from_type(
            processable_type=processable_type, config_values=config_values, instance_name=instance_name)


class SubProcessFactoryReadFromDb(SubProcessableFactory):
    """Factory used when getting a protocol from the database,  it read the protocol's processes
    from the DB

    :param SubProcessableFactory: [description]
    :type SubProcessableFactory: [type]
    """

    def _instantiate_processable(self, processable_uri: Optional[str],
                                 processable_type: Type[Processable],
                                 instance_name: str,
                                 node_json: Dict) -> ProcessableModel:
        if processable_uri is None:
            raise BadRequestException(
                f"Cannot instantiate the processable {instance_name} because it does not have an uri")

        return self._get_processable_from_db(processable_uri=processable_uri, processable_type=processable_type)


class SubProcessFactoryCreate(SubProcessableFactory):
    """Factory used to force creation of a processes when building a protocol

    :param SubProcessableFactory: [description]
    :type SubProcessableFactory: [type]
    """

    def _instantiate_processable(self, processable_uri: Optional[str],
                                 processable_type: Type[Processable],
                                 instance_name: str,
                                 node_json: Dict) -> ProcessableModel:

        return self._create_new_processable(processable_type=processable_type, instance_name=instance_name,
                                            node_json=node_json)


class SubProcessFactoryUpdate(SubProcessableFactory):
    """Factory used to get the processes or create a new one when building a protocol

    :param SubProcessableFactory: [description]
    :type SubProcessableFactory: [type]
    """

    def _instantiate_processable(self, processable_uri: Optional[str],
                                 processable_type: Type[Processable],
                                 instance_name: str,
                                 node_json: Dict) -> ProcessableModel:

        if processable_uri is not None:
            processable_model: ProcessableModel = self._get_processable_from_db(
                processable_uri=processable_uri, processable_type=processable_type)

            # Update the processable config
            if node_json.get('config'):
                params = node_json.get('config').get("data", {}).get("params", {})
                processable_model.config.set_params(params)

            return processable_model

        else:
            return self._create_new_processable(processable_type=processable_type, instance_name=instance_name,
                                                node_json=node_json)

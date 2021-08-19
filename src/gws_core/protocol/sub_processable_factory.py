

from typing import Optional, Type

from gws_core.process.process import Process

from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..process.process_model import ProcessModel
from ..process.processable import Processable
from ..process.processable_model import ProcessableModel


class SubProcessableFactory():
    """Factory used by the ProtocolModel builder to instantiate processs of Protocol
    """

    def instantiate_processable(self, processable_uri: Optional[str],
                                processable_type: Type[Processable],
                                instance_name: str) -> ProcessableModel:
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
                                instance_name: str) -> ProcessableModel:
        """Method to instantiate a new processable
        """
        from ..process.processable_factory import ProcessableFactory

        # if this is a process
        if issubclass(processable_type, Process):
            return ProcessableFactory.create_process_from_type(
                process_type=processable_type, instance_name=instance_name)
        else:
            # if this is a protocol
            # create an empty protocol
            return ProcessableFactory.create_protocol_from_type(
                protocol_type=processable_type, instance_name=instance_name)


class SubProcessFactoryReadFromDb(SubProcessableFactory):
    """Factory used when getting a protocol from the database,  it read the protocol's processes
    from the DB

    :param SubProcessableFactory: [description]
    :type SubProcessableFactory: [type]
    """

    def instantiate_processable(self, processable_uri: Optional[str],
                                processable_type: Type[Processable],
                                instance_name: str) -> ProcessableModel:
        if processable_uri is None:
            raise BadRequestException(
                f"Cannot instantiate the processable {instance_name} because it does not have an uri")

        return self._get_processable_from_db(processable_uri=processable_uri, processable_type=processable_type)


class SubProcessFactoryCreate(SubProcessableFactory):
    """Factory used to force creation of a processes when building a protocol

    :param SubProcessableFactory: [description]
    :type SubProcessableFactory: [type]
    """

    def instantiate_processable(self, processable_uri: Optional[str],
                                processable_type: Type[Processable],
                                instance_name: str) -> ProcessableModel:

        return self._create_new_processable(processable_type=processable_type, instance_name=instance_name)


class SubProcessFactoryUpdate(SubProcessableFactory):
    """Factory used to get the processes or create a new one when building a protocol

    :param SubProcessableFactory: [description]
    :type SubProcessableFactory: [type]
    """

    def instantiate_processable(self, processable_uri: Optional[str],
                                processable_type: Type[Processable],
                                instance_name: str) -> ProcessableModel:

        if processable_uri is not None:
            return self._get_processable_from_db(processable_uri=processable_uri, processable_type=processable_type)
        else:
            return self._create_new_processable(processable_type=processable_type, instance_name=instance_name)

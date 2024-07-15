

from abc import abstractmethod
from typing import Dict, Optional

from gws_core.model.typing import Typing
from gws_core.process.process_types import ProcessMinimumDTO
from gws_core.protocol.protocol_dto import ProtocolMinimumDTO

from ..task.task_model import TaskModel
from .process_model import ProcessModel


class ProtocolSubProcessBuilder():
    """Builder used by the ProtocolModel build method to instantiate processs of Protocol base on a DTO
    """

    @abstractmethod
    def instantiate_processes(self) -> Dict[str, ProcessModel]:
        pass


class SubProcessBuilderReadFromDb(ProtocolSubProcessBuilder):
    """Factory used when getting a protocol from the database,  it read the protocol's processes
    from the DB
    """

    protocol_config: ProtocolMinimumDTO

    def __init__(self, protocol_config: ProtocolMinimumDTO) -> None:
        super().__init__()
        self.protocol_config = protocol_config

    def instantiate_processes(self) -> Dict[str, ProcessModel]:
        processes: Dict[str, ProcessModel] = {}
        for instance_name, process_dto in self.protocol_config.nodes.items():
            processes[instance_name] = self.instantiate_process(process_dto)
        return processes

    def instantiate_process(self, process_dto: ProcessMinimumDTO) -> ProcessModel:
        proc_id: str = process_dto.id

        proc_type_str: str = process_dto.process_typing_name
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

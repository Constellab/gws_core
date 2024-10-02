

from typing import Optional, Set

from gws_core.io.connector import Connector
from gws_core.io.ioface import IOface
from gws_core.process.process_model import ProcessModel
from gws_core.protocol.protocol_dto import ProtocolUpdateDTO
from gws_core.protocol.protocol_model import ProtocolModel


class ProtocolUpdate():
    """Result object for a protocol update

    If a process is provided, it means that the process has been updated
    If a connector is provided, it means that a new connector has been added

    If protocol_updated is True, it means that the protocol or other processes has been updated
    """

    process: Optional[ProcessModel]
    connector: Optional[Connector]
    ioface: Optional[IOface]
    protocol: ProtocolModel
    # set of sub protocols that have been updated
    sub_protocols: Optional[Set[ProtocolModel]]

    protocol_updated: bool

    def __init__(self, protocol: ProtocolModel,
                 protocol_updated: bool = False,
                 process: Optional[ProcessModel] = None,
                 connector: Optional[Connector] = None,
                 ioface: Optional[IOface] = None,
                 sub_protocols: Optional[Set[ProtocolModel]] = None) -> None:
        self.process = process
        self.connector = connector
        self.ioface = ioface
        self.protocol = protocol
        self.protocol_updated = protocol_updated
        self.sub_protocols = sub_protocols or set()

    def to_dto(self) -> ProtocolUpdateDTO:
        return ProtocolUpdateDTO(
            process=self.process.to_dto() if self.process else None,
            link=self.connector.to_dto() if self.connector else None,
            ioface=self.ioface.to_dto() if self.ioface else None,
            protocol_updated=self.protocol_updated,
            protocol=self.protocol.to_protocol_dto() if self.protocol_updated else None,
            sub_protocols=[p.to_protocol_dto() for p in self.sub_protocols]
        )

    def merge(self, protocol_update: 'ProtocolUpdate') -> 'ProtocolUpdate':
        """Merge the current protocol update with another one
        """
        self.process = self.process or protocol_update.process
        self.connector = self.connector or protocol_update.connector
        self.ioface = self.ioface or protocol_update.ioface
        self.protocol_updated = self.protocol_updated or protocol_update.protocol_updated
        self.sub_protocols = self.sub_protocols.union(protocol_update.sub_protocols)
        return self

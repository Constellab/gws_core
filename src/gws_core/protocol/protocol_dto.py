# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, Optional

from pydantic import BaseModel

from gws_core.io.connector import Connector
from gws_core.process.process_model import ProcessModel
from gws_core.protocol.protocol_model import ProtocolModel


class ProtocolUpdateDTO():
    """Result object for a protocol update

    If a process is provided, it means that the process has been updated
    If a connector is provided, it means that a new connector has been added

    If protocol_updated is True, it means that the protocol or other processes has been updated
    """

    process: Optional[ProcessModel]
    connector: Optional[Connector]
    protocol: ProtocolModel

    protocol_updated: bool

    def __init__(self, protocol: ProtocolModel,
                 protocol_updated: bool = False,
                 process: Optional[ProcessModel] = None,
                 connector: Optional[Connector] = None) -> None:
        self.process = process
        self.connector = connector
        self.protocol = protocol
        self.protocol_updated = protocol_updated

    def to_json(self) -> Dict:
        json_ = {
            "process": self.process.to_json(deep=True) if self.process else None,
            "link": self.connector.to_json() if self.connector else None,
            "protocol_updated": self.protocol_updated
        }

        if self.protocol_updated:
            json_["protocol"] = self.protocol.to_json(deep=True)

        return json_

    def merge(self, protocol_update: 'ProtocolUpdateDTO') -> 'ProtocolUpdateDTO':
        """Merge the current protocol update with another one
        """
        self.process = self.process or protocol_update.process
        self.connector = self.connector or protocol_update.connector
        self.protocol_updated = self.protocol_updated or protocol_update.protocol_updated
        return self


class AddConnectorDTO(BaseModel):
    output_process_name: str = None
    output_port_name: str = None
    input_process_name: str = None
    input_port_name: str = None

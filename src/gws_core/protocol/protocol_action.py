# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict

from gws_core.io.connector import Connector
from gws_core.process.process_model import ProcessModel
from pydantic import BaseModel


class AddProcessWithLink():

    process_model: ProcessModel

    connector: Connector

    def __init__(self, process_model: ProcessModel, connector: Connector) -> None:
        self.process_model = process_model
        self.connector = connector

    def to_json(self) -> Dict:
        return {
            "process": self.process_model.to_json(deep=True),
            "link": self.connector.to_json()
        }


class AddConnectorDTO(BaseModel):
    output_process_name: str = None
    output_port_name: str = None
    input_process_name: str = None
    input_port_name: str = None

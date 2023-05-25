# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import final

from gws_core.process.process_model import ProcessModel
from gws_core.protocol.protocol_types import InterfaceDict

from ..resource.resource_model import ResourceModel
from .port import InPort, OutPort, Port


class IOface:
    name: str = None

    source_process: ProcessModel = None
    target_process: ProcessModel = None

    source_port_name: str = None
    target_port_name: str = None

    def __init__(self, name: str, source_process: ProcessModel, target_process: ProcessModel,
                 source_port_name: str, target_port_name: str):

        self.name = name
        self.source_process = source_process
        self.target_process = target_process
        self.source_port_name = source_port_name
        self.target_port_name = target_port_name

    @property
    def source_port(self) -> Port:
        return self.source_process.in_port(self.source_port_name)

    @property
    def target_port(self) -> Port:
        return self.target_process.in_port(self.target_port_name)

    def reset(self):
        if self.source_port:
            self.source_port.reset()

        if self.target_port:
            self.target_port.reset()

    def to_json(self, deep: bool = False) -> InterfaceDict:
        return {
            "name": self.name,
            "from": {
                "node": self.source_process.instance_name,
                "port": self.source_port_name,
            },
            "to": {
                "node": self.target_process.instance_name,
                "port": self.target_port_name,
            },
        }


@final
class Interface(IOface):
    source_port: InPort = None
    target_port: InPort = None

    @property
    def source_port(self) -> InPort:
        return self.source_process.in_port(self.source_port_name)

    @property
    def target_port(self) -> InPort:
        return self.target_process.in_port(self.target_port_name)

    def set_resource(self, resource_model: ResourceModel):
        self.source_port.resource_model = resource_model
        self.target_port.resource_model = resource_model

    def to_json(self) -> InterfaceDict:
        _json = super().to_json()
        _json["from"]["node"] = ":parent:"
        return _json


@final
class Outerface(IOface):
    source_port: OutPort = None
    target_port: OutPort = None

    @property
    def source_port(self) -> OutPort:
        return self.source_process.out_port(self.source_port_name)

    @property
    def target_port(self) -> OutPort:
        return self.target_process.out_port(self.target_port_name)

    def get_resource(self) -> ResourceModel:
        return self.source_port.resource_model

    def to_json(self) -> InterfaceDict:
        _json = super().to_json()
        _json["to"]["node"] = ":parent:"
        return _json

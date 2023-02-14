# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from json import dumps, loads
from typing import Dict

from typing_extensions import TypedDict

from gws_core.core.model.db_field import SerializableObject


class ProcessLayout(TypedDict):
    x: float
    y: float


class ProtocolLayoutDict(TypedDict):
    process_layouts: Dict[str, ProcessLayout]
    interface_layouts: Dict[str, ProcessLayout]
    outerface_layouts: Dict[str, ProcessLayout]


class ProtocolLayout(SerializableObject):
    """object to store the layout (position) of a protocol's processes
    """

    # layout of the processes, key = process instance name
    process_layouts: Dict[str, ProcessLayout]
    interface_layouts: Dict[str, ProcessLayout]
    outerface_layouts: Dict[str, ProcessLayout]

    def __init__(self, json_: ProtocolLayoutDict = None) -> None:
        super().__init__()

        if json_:
            self.process_layouts = json_.get('process_layouts', {})
            self.interface_layouts = json_.get('interface_layouts', {})
            self.outerface_layouts = json_.get('outerface_layouts', {})
        else:
            self.process_layouts = {}
            self.interface_layouts = {}
            self.outerface_layouts = {}

    def serialize(self) -> str:
        return dumps(self.to_json())

    def to_json(self) -> ProtocolLayoutDict:
        return {'process_layouts': self.process_layouts,
                'interface_layouts': self.interface_layouts,
                'outerface_layouts': self.outerface_layouts}

    def set_process(self, instance_name: str, layout: ProcessLayout) -> None:
        self.process_layouts[instance_name] = layout

    def remove_process(self, instance_name: str) -> None:
        if instance_name in self.process_layouts:
            del self.process_layouts[instance_name]

    def set_interface(self, interface_name: str,  layout: ProcessLayout) -> None:
        self.interface_layouts[interface_name] = layout

    def remove_interface(self, interface_name: str) -> None:
        if interface_name in self.interface_layouts:
            del self.process_layouts[interface_name]

    def set_outerface(self, outerface_name: str,  layout: ProcessLayout) -> None:
        self.outerface_layouts[outerface_name] = layout

    def remove_outerface(self, outerface_name: str) -> None:
        if outerface_name in self.outerface_layouts:
            del self.process_layouts[outerface_name]

    def get_process(self, instance_name: str) -> ProcessLayout:
        if instance_name not in self.process_layouts:
            return None
        return self.process_layouts.get(instance_name)

    @classmethod
    def deserialize(cls, value: str) -> 'ProtocolLayout':
        if not value:
            return ProtocolLayout()
        else:
            return ProtocolLayout(loads(value))

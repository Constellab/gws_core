

from json import loads
from typing import Dict, Optional

from gws_core.core.model.db_field import SerializableObject
from gws_core.core.model.model_dto import BaseModelDTO


class ProcessLayoutDTO(BaseModelDTO):
    x: Optional[float]
    y: Optional[float]


class ProtocolLayoutDTO(BaseModelDTO):
    process_layouts: Dict[str, ProcessLayoutDTO]
    interface_layouts: Dict[str, ProcessLayoutDTO]
    outerface_layouts: Dict[str, ProcessLayoutDTO]


class ProtocolLayout(SerializableObject):
    """object to store the layout (position) of a protocol's processes
    """

    # layout of the processes, key = process instance name
    process_layouts: Dict[str, ProcessLayoutDTO]
    interface_layouts: Dict[str, ProcessLayoutDTO]
    outerface_layouts: Dict[str, ProcessLayoutDTO]

    def __init__(self, layout_dto: ProtocolLayoutDTO = None) -> None:
        super().__init__()

        if layout_dto:
            self.process_layouts = layout_dto.process_layouts
            self.interface_layouts = layout_dto.interface_layouts
            self.outerface_layouts = layout_dto.outerface_layouts
        else:
            self.process_layouts = {}
            self.interface_layouts = {}
            self.outerface_layouts = {}

    def serialize(self) -> str:
        return self.to_dto().to_json_str()

    def to_dto(self) -> ProtocolLayoutDTO:
        return ProtocolLayoutDTO(
            process_layouts=self.process_layouts,
            interface_layouts=self.interface_layouts,
            outerface_layouts=self.outerface_layouts
        )

    def set_process(self, instance_name: str, layout: ProcessLayoutDTO) -> None:
        self.process_layouts[instance_name] = layout

    def remove_process(self, instance_name: str) -> None:
        if instance_name in self.process_layouts:
            del self.process_layouts[instance_name]

    def set_interface(self, interface_name: str,  layout: ProcessLayoutDTO) -> None:
        self.interface_layouts[interface_name] = layout

    def remove_interface(self, interface_name: str) -> None:
        if interface_name in self.interface_layouts:
            del self.interface_layouts[interface_name]

    def set_outerface(self, outerface_name: str,  layout: ProcessLayoutDTO) -> None:
        self.outerface_layouts[outerface_name] = layout

    def remove_outerface(self, outerface_name: str) -> None:
        if outerface_name in self.outerface_layouts:
            del self.outerface_layouts[outerface_name]

    def get_process(self, instance_name: str) -> ProcessLayoutDTO:
        if instance_name not in self.process_layouts:
            return None
        return self.process_layouts.get(instance_name)

    @classmethod
    def deserialize(cls, value: str) -> 'ProtocolLayout':
        if not value:
            return ProtocolLayout()
        else:
            return ProtocolLayout(ProtocolLayoutDTO.from_json(loads(value)))

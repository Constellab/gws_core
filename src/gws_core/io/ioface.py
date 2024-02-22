# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict

from gws_core.protocol.protocol_dto import IOFaceDTO


class IOface:
    name: str = None

    # For interface, this is the process that receives the resource from interface
    # For outerface, this is the process that sends the resource to outerface
    process_instance_name: str = None
    port_name: str = None

    def __init__(self, name: str,
                 process_instance_name: str, port_name: str):

        self.name = name
        self.process_instance_name = process_instance_name
        self.port_name = port_name

    def to_dto(self) -> IOFaceDTO:
        return IOFaceDTO(
            name=self.name,
            process_instance_name=self.process_instance_name,
            port_name=self.port_name
        )

    @classmethod
    def load_from_dto(cls, dto: IOFaceDTO) -> 'IOface':
        return IOface(
            name=dto.name,
            process_instance_name=dto.process_instance_name,
            port_name=dto.port_name
        )

    @classmethod
    def load_from_dto_dict(cls, iofaces: Dict[str, IOFaceDTO]) -> Dict[str, 'IOface']:
        return {name: cls.load_from_dto(dto) for name, dto in iofaces.items()}

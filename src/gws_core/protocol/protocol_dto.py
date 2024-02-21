# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, List, Optional

from pydantic import Field

from gws_core.config.config_dto import ConfigSimpleDTO
from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.io.io_dto import IODTO
from gws_core.io.io_specs import IOSpecsDTO
from gws_core.model.typing_dto import TypingFullDTO
from gws_core.process.process_dto import ProcessDTO, ProcessTypeDTO
from gws_core.process.process_types import ProcessMinimumDTO
from gws_core.protocol.protocol_layout import ProtocolLayoutDTO


class ConnectorPartDict(BaseModelDTO):
    node: str
    port: str


class ConnectorDTO(BaseModelDTO):
    from_: ConnectorPartDict = Field(alias='from')
    to: ConnectorPartDict

    # Override the method to use the alias in serialization
    def dict(self, *args, **kwargs):
        kwargs['by_alias'] = True
        return super().dict(*args, **kwargs)

    def json(self, *args, **kwargs):
        kwargs['by_alias'] = True
        return super().json(*args, **kwargs)


class InterfaceDTO(BaseModelDTO):
    name: str
    from_: ConnectorPartDict = Field(alias='from')
    to: ConnectorPartDict

    # Override the method to use the alias in serialization
    def dict(self, *args, **kwargs):
        kwargs['by_alias'] = True
        return super().dict(*args, **kwargs)

    def json(self, *args, **kwargs):
        kwargs['by_alias'] = True
        return super().json(*args, **kwargs)


class ProtocolConfigDTO(BaseModelDTO):
    nodes: Dict[str, 'ProcessConfigDTO']
    links: List[ConnectorDTO]
    interfaces: Dict[str, InterfaceDTO]
    outerfaces: Dict[str, InterfaceDTO]
    layout: Optional[ProtocolLayoutDTO]


# set this type here to avoid circular import files
class ProcessConfigDTO(BaseModelDTO):
    process_typing_name: str
    instance_name: str
    config: ConfigSimpleDTO
    name: str
    brick_version: str
    inputs: IODTO
    outputs: IODTO
    status: str
    process_type: ProcessTypeDTO
    # for sub protocol, recursive graph
    graph: Optional[ProtocolConfigDTO] = None


# call this method to set the type of the recursive graph
ProtocolConfigDTO.update_forward_refs()


class ProtocolMinimumDTO(BaseModelDTO):
    nodes: Dict[str, ProcessMinimumDTO]
    links: List[ConnectorDTO]
    interfaces: Dict[str, InterfaceDTO]
    outerfaces: Dict[str, InterfaceDTO]


class ProtocolFullDTO(BaseModelDTO):
    nodes: Dict[str, ProcessDTO]
    links: List[ConnectorDTO]
    interfaces: Dict[str, InterfaceDTO]
    outerfaces: Dict[str, InterfaceDTO]
    layout: Optional[ProtocolLayoutDTO]


class ProtocolDTO(ProcessDTO):
    data: ProtocolFullDTO


class ExperimentProtocolDTO(BaseModelDTO):
    version: int
    data: ProcessConfigDTO

################################### ROUTES DTOs ###################################


class ProtocolUpdateDTO(BaseModelDTO):
    process: Optional[ProcessDTO]
    link: Optional[ConnectorDTO]
    protocol_updated: bool
    protocol: Optional[ProtocolDTO]
    sub_protocols: Optional[List[ProtocolDTO]]


class AddConnectorDTO(BaseModelDTO):
    output_process_name: str
    output_port_name: str
    input_process_name: str
    input_port_name: str


class ProtocolTypingFullDTO(TypingFullDTO):
    input_specs: Optional[IOSpecsDTO] = None
    output_specs: Optional[IOSpecsDTO] = None
    config_specs: Optional[dict] = None

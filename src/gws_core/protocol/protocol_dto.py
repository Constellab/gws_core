# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Optional

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.io.io_spec import IOSpecDTO
from gws_core.model.typing_dto import TypingFullDTO
from gws_core.process.process_dto import ProcessDTO


class ProtocolDTO(ProcessDTO):
    data: dict


class ProtocolUpdateDTO(BaseModelDTO):
    process: Optional[ProcessDTO]
    # TODO TO type
    link: Optional[dict]
    protocol_updated: bool
    protocol: Optional[ProtocolDTO]


class AddConnectorDTO(BaseModelDTO):
    output_process_name: str
    output_port_name: str
    input_process_name: str
    input_port_name: str


class ProtocolTypingFullDTO(TypingFullDTO):
    input_specs: Optional[IOSpecDTO] = None
    output_specs: Optional[IOSpecDTO] = None
    config_specs: Optional[dict] = None

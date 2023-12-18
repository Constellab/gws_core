# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, Optional

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.io.io_spec import IOSpecDTO
from gws_core.io.io_specs import IOSpecsType


class PortDTO(BaseModelDTO):
    resource_id: Optional[str]
    specs: IOSpecDTO


class IODTO(BaseModelDTO):
    ports: Dict[str, PortDTO] = {}
    type: IOSpecsType = 'normal'
    additional_info: dict = None



from typing import Dict, Optional

from gws_core.config.param.param_types import ParamSpecDTO
from gws_core.io.io_specs import IOSpecsDTO
from gws_core.model.typing_dto import TypingFullDTO


class TaskTypingDTO(TypingFullDTO):
    input_specs: Optional[IOSpecsDTO] = None
    output_specs: Optional[IOSpecsDTO] = None
    config_specs: Optional[Dict[str, ParamSpecDTO]] = None
    additional_data: Optional[dict] = None

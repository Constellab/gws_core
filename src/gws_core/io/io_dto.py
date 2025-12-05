
from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.io.io_spec import IOSpecDTO
from gws_core.io.io_specs import IOSpecsType


class PortDTO(BaseModelDTO):
    resource_id: str | None
    specs: IOSpecDTO


class IODTO(BaseModelDTO):
    ports: dict[str, PortDTO] = {}
    type: IOSpecsType = "normal"
    additional_info: dict | None = None

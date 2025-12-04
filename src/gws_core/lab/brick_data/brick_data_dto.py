from typing import Literal

from gws_core.core.model.model_dto import BaseModelDTO


class BrickDataDTO(BaseModelDTO):
    brick_name: str
    fs_node_name: str
    fs_node_size: int
    fs_node_path: str
    fs_node_type: Literal["file", "folder"]

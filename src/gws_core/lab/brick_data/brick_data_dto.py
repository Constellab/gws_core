# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Literal

from gws_core.core.model.model_dto import BaseModelDTO


class BrickDataDTO(BaseModelDTO):

    brick_name: str
    fs_node_name: str
    fs_node_size: int
    fs_node_path: str
    fs_node_type: Literal['file', 'folder']

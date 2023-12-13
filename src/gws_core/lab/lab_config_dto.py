# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from gws_core.brick.brick_dto import BrickVersion
from gws_core.core.model.model_dto import BaseModelDTO


class LabConfigModelDTO(BaseModelDTO):
    version: int
    brick_versions: List[BrickVersion]

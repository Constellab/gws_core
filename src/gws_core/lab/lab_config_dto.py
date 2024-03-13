

from typing import List

from gws_core.brick.brick_dto import BrickVersion
from gws_core.core.model.model_dto import BaseModelDTO


class LabConfigModelDTO(BaseModelDTO):
    version: int
    brick_versions: List[BrickVersion]

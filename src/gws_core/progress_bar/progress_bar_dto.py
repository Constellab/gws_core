# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from datetime import datetime
from typing import Optional

from gws_core.core.model.model_dto import BaseModelDTO


class ProgressBarDTO(BaseModelDTO):
    id: str
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    current_value: float
    elapsed_time: float
    second_start: Optional[datetime]

# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from datetime import datetime

from pydantic import BaseModel


class ModelDTO(BaseModel):
    """
    ModelDTO class.
    """
    id: str
    created_at: datetime
    last_modified_at: datetime

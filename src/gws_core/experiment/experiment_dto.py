# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Optional

from pydantic import BaseModel


# DTO to create/update an experiment
class ExperimentDTO(BaseModel):
    study_uri: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    graph: Optional[dict] = None

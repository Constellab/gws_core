
from typing import Optional

from pydantic import BaseModel


# DTO to create/update an experiment
class ExperimentDTO(BaseModel):
    study_uri: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    graph: Optional[dict] = None

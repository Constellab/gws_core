# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Optional

from pydantic import BaseModel

from ..study.study_dto import StudyDto


# DTO to create/update an experiment
class ExperimentDTO(BaseModel):
    study: Optional[StudyDto] = None
    title: Optional[str] = None
    description: Optional[str] = None

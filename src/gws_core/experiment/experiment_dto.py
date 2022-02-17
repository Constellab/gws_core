# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, Optional, TypedDict

from pydantic import BaseModel

from ..project.project_dto import ProjectDto


# DTO to create/update an experiment
class ExperimentDTO(BaseModel):
    project: Optional[ProjectDto] = None
    title: str = None


class SaveExperimentToCentralDTO(TypedDict):
    experiment: dict
    protocol: dict
    lab_config: dict

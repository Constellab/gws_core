# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Optional

from pydantic import BaseModel

from ..project.project_dto import ProjectDto


class ReportDTO(BaseModel):
    title: str = None
    project: Optional[ProjectDto] = None


from typing import List

from fastapi.param_functions import Depends

from ..core_app import core_app
from ..user.auth_service import AuthService
from ..user.user_dto import UserData
from .project_dto import ProjectDto
from .project_service import ProjectService


@core_app.get("/project", tags=["Project"])
async def read_user_me(_: UserData = Depends(AuthService.check_user_access_token)) -> List[ProjectDto]:
    """
    Get the list of available projects.
    """

    return ProjectService.get_available_projects()

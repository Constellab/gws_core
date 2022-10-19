
from typing import Dict, List

from fastapi.param_functions import Depends
from gws_core.core.classes.jsonable import ListJsonable

from ..core_app import core_app
from ..user.auth_service import AuthService
from ..user.user_dto import UserData
from .project_dto import ProjectDto
from .project_service import ProjectService


@core_app.get("/project", tags=["Project"])
def read_user_me(_: UserData = Depends(AuthService.check_user_access_token)) -> List[ProjectDto]:
    """
    Get the list of available projects.
    """

    return ProjectService.get_available_projects()


@core_app.post("/project/synchronize", tags=["Project"])
def synchronize_project(_: UserData = Depends(AuthService.check_user_access_token)) -> ProjectDto:
    """
    Synchronize the projects from central
    """

    return ProjectService.synchronize_central_projects()


@core_app.get("/project/trees", tags=["Project"])
def get_project_trees(_: UserData = Depends(AuthService.check_user_access_token)) -> Dict:
    """
    Get the list of available projects with children.
    """

    return ListJsonable(ProjectService.get_project_trees()).to_json(deep=True)

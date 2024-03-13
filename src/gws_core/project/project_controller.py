

from typing import List

from fastapi.param_functions import Depends

from gws_core.project.project_dto import ProjectTreeDTO

from ..core_controller import core_app
from ..user.auth_service import AuthService
from .project_service import ProjectService


@core_app.post("/project/synchronize", tags=["Project"])
def synchronize_project(_=Depends(AuthService.check_user_access_token)) -> None:
    """
    Synchronize the projects from space
    """

    ProjectService.synchronize_all_space_projects()


@core_app.get("/project/trees", tags=["Project"])
def get_project_trees(_=Depends(AuthService.check_user_access_token)) -> List[ProjectTreeDTO]:
    """
    Get the list of available projects with children.
    """

    projects = ProjectService.get_project_trees()
    return [project.to_tree_dto() for project in projects]

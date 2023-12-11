# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import List

from fastapi.param_functions import Depends

from gws_core.core.classes.jsonable import ListJsonable
from gws_core.project.project_dto import ProjectDTO

from ..core_app import core_app
from ..user.auth_service import AuthService
from .project_service import ProjectService


@core_app.post("/project/synchronize", tags=["Project"])
def synchronize_project(_=Depends(AuthService.check_user_access_token)) -> None:
    """
    Synchronize the projects from space
    """

    return ProjectService.synchronize_all_space_projects()


@core_app.get("/project/trees", tags=["Project"])
def get_project_trees(_=Depends(AuthService.check_user_access_token)) -> List[ProjectDTO]:
    """
    Get the list of available projects with children.
    """

    return ListJsonable(ProjectService.get_project_trees()).to_json(deep=True)

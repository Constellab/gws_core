

from gws_core.project.project import Project
from gws_core.project.project_dto import ProjectLevelStatus

from ..core.console.console import Console


class GTest(Console):
    """
    GTest class.

    Provides functionalities to initilize unit testing environments
    """

    @classmethod
    def create_default_project(cls) -> Project:
        """
        Get a default Project
        """
        return Project(title="Default project",
                       description="Project description",
                       level_status=ProjectLevelStatus.LEAF).save()

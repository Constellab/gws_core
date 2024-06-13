

from gws_core.project.project import Project
from gws_core.project.project_dto import ProjectLevelStatus
from gws_core.user.user import User
from gws_core.user.user_group import UserGroup

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

    @classmethod
    def get_test_user(cls) -> User:
        """
        Get a default User
        """
        return User(email="test@gencovery.com",
                    first_name="Test",
                    last_name="User",
                    group=UserGroup.USER)

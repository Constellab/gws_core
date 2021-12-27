# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.project.project import Project

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
        return Project(title="Default project", description="Project description").save()

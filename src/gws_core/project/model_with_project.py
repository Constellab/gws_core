# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from peewee import ForeignKeyField
from peewee import Model as PeeweeModel

from gws_core.project.project import Project


class ModelWithProject(PeeweeModel):

    project: Project = ForeignKeyField(Project, null=True)

    @classmethod
    def clear_project(cls, projects: List[Project]) -> None:
        """
        Clear project from all the entities that have the project
        """

        cls.update(project=None).where(cls.project.in_(projects)).execute()

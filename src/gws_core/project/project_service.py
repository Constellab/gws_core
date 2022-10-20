
from threading import Thread
from typing import List

from ..central.central_service import CentralService
from ..core.service.base_service import BaseService
from .project import Project
from .project_dto import CentralProject


class ProjectService(BaseService):

    @classmethod
    def get_project_trees(cls) -> List[Project]:
        return list(Project.get_roots())

    @classmethod
    def synchronize_central_projects_async(cls) -> None:
        """Synchronize the projects from central in the lab without blocking the thread"""
        thread = Thread(target=cls.synchronize_central_projects)
        thread.start()

    @classmethod
    def synchronize_central_projects(cls) -> None:
        """Method that retrieve the project from central and synchronize them into the lab
        """

        project: List[CentralProject] = CentralService.get_projects()

        for central_project in project:
            cls._synchronize_project(central_project, None)

    @classmethod
    def _synchronize_project(cls, project: CentralProject, parent: Project) -> None:
        """Method that synchronize a project from central into the lab
        """

        lab_project: Project = Project.get_by_id(project['id'])

        if lab_project is None:
            lab_project = Project()
            lab_project.id = project['id']

        # update other fields
        lab_project.code = project['code']
        lab_project.title = project['title']
        lab_project.parent = parent
        lab_project.save()

        if 'children' in project:
            for child in project['children']:
                cls._synchronize_project(child, lab_project)

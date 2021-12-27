
from typing import List

from ..central.central_service import CentralService
from ..core.service.base_service import BaseService
from ..core.utils.logger import Logger
from .project import Project
from .project_dto import CentralProject, ProjectDto


class ProjectService(BaseService):

    @classmethod
    def get_available_projects(cls) -> List[ProjectDto]:

        central_projects: List[ProjectDto] = cls.get_central_projects()

        lab_projects: List[ProjectDto] = cls.get_lab_projects()

        # Add the lab projects to central project and avoid duplicate
        for lab_project in lab_projects:
            if lab_project not in central_projects:
                central_projects.append(lab_project)

        return central_projects

    @classmethod
    def get_central_projects(cls) -> List[ProjectDto]:
        central_projects: List[CentralProject]
        try:
            central_projects = CentralService.get_current_user_projects()
        except Exception as err:
            Logger.log_exception_stack_trace(err)
            return []

        projects_dto: List[ProjectDto] = []
        for project in central_projects:
            projects_dto.append(
                ProjectDto(
                    id=project['id'],
                    title=project['title'],
                    description=project['description']))
        return projects_dto

    @classmethod
    def get_lab_projects(cls) -> List[ProjectDto]:
        projects: List[Project] = list(Project.select())

        projects_dto: List[ProjectDto] = []
        for project in projects:
            projects_dto.append(ProjectDto(id=project.id, title=project.title, description=project.description))
        return projects_dto

    @classmethod
    def get_or_create_project_from_dto(cls, project_dto: ProjectDto) -> Project:
        """Retreive the project based on a DTO and if it doesn't exists, it creates the project
        """
        if project_dto is None or project_dto.id is None:
            return None

        project: Project = Project.get_by_id(project_dto.id)

        if project is not None:
            return project

        # Create the project form the DTO
        project = Project()
        project.id = project_dto.id
        project.title = project_dto.title
        project.description = project_dto.description
        return project.save()

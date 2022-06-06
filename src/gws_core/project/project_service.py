
from typing import List

from ..central.central_service import CentralService
from ..core.service.base_service import BaseService
from ..core.utils.logger import Logger
from ..core.utils.settings import Settings
from .project import Project
from .project_dto import CentralProject, ProjectDto


class ProjectService(BaseService):

    @classmethod
    def get_available_projects(cls) -> List[ProjectDto]:

        central_projects: List[ProjectDto] = cls.get_central_projects()

        lab_projects: List[Project] = cls.get_lab_projects()

        # Add the lab projects to central project and avoid duplicate
        for lab_project in lab_projects:
            # find the project in central by id
            central_project = [p for p in central_projects if p.id == lab_project.id]

            # if the project exist in central, refresh the project info if necessary
            if len(central_project) >= 0:
                cls._refresh_lab_project(lab_project, central_project[0])
            # if the project is in the lab but not in central (should not happen=, add it to the list to return
            else:
                central_projects.append(
                    ProjectDto(
                        id=lab_project.id, title=lab_project.title,
                        description=lab_project.description))

        return central_projects

    @classmethod
    def _refresh_lab_project(cls, lab_project: Project, central_project: ProjectDto) -> None:
        """ Update the project store in the lab if information where change in central"""
        if central_project.title != lab_project.title or \
                central_project.description != lab_project.description:
            lab_project.title = central_project.title
            lab_project.description = central_project.description
            lab_project.save()

    @classmethod
    def get_central_projects(cls) -> List[ProjectDto]:
        central_projects: List[CentralProject]
        try:
            central_projects = CentralService.get_current_user_projects()
        except Exception as err:
            if not Settings.is_local_env():
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
    def get_lab_projects(cls) -> List[Project]:
        return list(Project.select())

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



from typing import List

from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.exception.gws_exceptions import GWSException
from gws_core.core.utils.logger import Logger
from gws_core.experiment.experiment import Experiment
from gws_core.project.model_with_project import ModelWithProject
from gws_core.report.report import Report
from gws_core.resource.resource_model import ResourceModel
from gws_core.space.space_service import SpaceService

from .project import Project
from .project_dto import SpaceProject


class ProjectService():

    entity_with_projects: List[ModelWithProject] = [Experiment, Report, ResourceModel]

    @classmethod
    def get_project_trees(cls) -> List[Project]:
        return list(Project.get_roots())

    @classmethod
    def synchronize_all_space_projects(cls) -> None:
        """
        Synchronize all the projects from space
        """

        Logger.info("Synchronizing projects from space")

        try:
            space_projects = SpaceService.get_all_lab_projects()
            for space_project in space_projects:
                cls.synchronize_space_project(space_project)
            Logger.info(f"{len(space_projects)} projects synchronized from space")
        except Exception as err:
            Logger.error(f"Error while synchronizing projects from space: {err}")
            raise err

    @classmethod
    def synchronize_space_project(cls, project: SpaceProject) -> None:
        """Method that synchronize a project from space into the lab
        """

        cls._synchronize_space_project(project, None)

    @classmethod
    def _synchronize_space_project(cls, project: SpaceProject, parent: Project) -> None:
        """Method that synchronize a project from space into the lab
        """

        lab_project: Project = Project.get_by_id(project.id)

        if lab_project is None:
            lab_project = Project()
            lab_project.id = project.id

        # update other fields
        lab_project.code = project.code
        lab_project.title = project.title
        lab_project.parent = parent
        lab_project.level_status = project.levelStatus
        lab_project.save()

        # delete children that are not in the space project
        if lab_project.children:
            for child in lab_project.children:
                if child.id not in [otherChild.id for otherChild in project.children]:
                    cls.delete_project(child.id)

        if project.children is not None:
            for child in project.children:
                cls._synchronize_space_project(child, lab_project)

    @classmethod
    def delete_project(cls, project_id: str) -> None:
        """Method that delete a project from the lab
        """
        project: Project = Project.get_by_id(project_id)

        if project is None:
            return

        projects = project.get_hierarchy_as_list()

        # check if one of the sync experiment is attached to the project
        if Experiment.select().where((Experiment.project.in_(projects)) & (Experiment.last_sync_at.is_null(False))).count() > 0:
            raise BadRequestException(detail=GWSException.DELETE_PROJECT_WITH_EXPERIMENTS.value,
                                      unique_code=GWSException.DELETE_PROJECT_WITH_EXPERIMENTS.name)

        # check if one of the report is attached to the project
        if Report.select().where((Report.project.in_(projects)) & (Report.last_sync_at.is_null(False))).count() > 0:
            raise BadRequestException(detail=GWSException.DELETE_PROJECT_WITH_REPORTS.value,
                                      unique_code=GWSException.DELETE_PROJECT_WITH_REPORTS.name)

        # Clear all objects that are using the project
        for entity in cls.entity_with_projects:
            entity.clear_project(projects)

        project.delete_instance()
        return None

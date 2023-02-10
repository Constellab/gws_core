# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from gws_core.central.central_service import CentralService
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.exception.gws_exceptions import GWSException
from gws_core.core.utils.logger import Logger
from gws_core.experiment.experiment import Experiment
from gws_core.report.report import Report

from ..core.service.base_service import BaseService
from .project import Project
from .project_dto import CentralProject


class ProjectService(BaseService):

    @classmethod
    def get_project_trees(cls) -> List[Project]:
        return list(Project.get_roots())

    @classmethod
    def synchronize_all_central_projects(cls) -> None:
        """
        Synchronize all the projects from central
        """

        Logger.info("Synchronizing projects from central")

        try:
            central_projects = CentralService.get_all_lab_projects()
            for central_project in central_projects:
                cls.synchronize_central_project(central_project)
            Logger.info(f"{len(central_projects)} projects synchronized from central")
        except Exception as err:
            Logger.error(f"Error while synchronizing projects from central: {err}")
            raise err

    @classmethod
    def synchronize_central_project(cls, project: CentralProject) -> None:
        """Method that synchronize a project from central into the lab
        """

        cls._synchronize_central_project(project, None)

    @classmethod
    def _synchronize_central_project(cls, project: CentralProject, parent: Project) -> None:
        """Method that synchronize a project from central into the lab
        """

        lab_project: Project = Project.get_by_id(project.id)

        if lab_project is None:
            lab_project = Project()
            lab_project.id = project.id

        # update other fields
        lab_project.code = project.code
        lab_project.title = project.title
        lab_project.parent = parent
        lab_project.save()

        if project.children is not None:
            for child in project.children:
                cls._synchronize_central_project(child, lab_project)

    @classmethod
    def delete_project(cls, project_id: str) -> None:
        """Method that delete a project from the lab
        """
        project: Project = Project.get_by_id(project_id)

        if project is None:
            return

        projects = project.get_hierarchy_as_list()

        # check if one of the experiment is attached to the project
        if Experiment.select().where(Experiment.project.in_(projects)).count() > 0:
            raise BadRequestException(GWSException.DELETE_PROJECT_WITH_EXPERIMENTS)

        # check if one of the report is attached to the project
        if Report.select().where(Report.project.in_(projects)).count() > 0:
            raise BadRequestException(GWSException.DELETE_PROJECT_WITH_REPORTS)

        project.delete_instance()

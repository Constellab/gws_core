

from typing import List

from gws_core import BaseTestCase
from gws_core.project.project import Project
from gws_core.project.project_dto import ProjectDto
from gws_core.project.project_service import ProjectService


class TestProject(BaseTestCase):

    def test_get_or_create_project(self):

        project_dto: ProjectDto = ProjectDto(id="caf61803-70e5-4ac3-9adb-53a35f65a2f1",
                                             title="Project", description="Description")

        project: Project = ProjectService.get_or_create_project_from_dto(project_dto)

        self.assertEqual(Project.select().count(), 1)
        self.assertEqual(project.id, "caf61803-70e5-4ac3-9adb-53a35f65a2f1")
        self.assertEqual(project.title, "Project")
        self.assertEqual(project.description, "Description")

        # Check that if we call the same project, it doesn't create a new one
        project: Project = ProjectService.get_or_create_project_from_dto(project_dto)
        self.assertEqual(Project.select().count(), 1)

        projects: List[Project] = ProjectService.get_available_projects()
        self.assertEqual(len(projects), 1)

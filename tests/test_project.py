# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core import BaseTestCase
from gws_core.experiment.experiment_service import ExperimentService
from gws_core.project.project import Project
from gws_core.project.project_dto import SpaceProject
from gws_core.project.project_service import ProjectService


# test_project
class TestProject(BaseTestCase):

    def test_get_or_create_project_with_children(self):

        space_project: SpaceProject = SpaceProject(**{
            "id": "caf61803-70e5-4ac3-9adb-53a35f65a2f1",
            "code": "Root",
            "title": "Root project",
            "children": [
                {
                    "id": "caf61803-70e5-4ac3-9adb-53a35f65a2f2",
                    "code": "WP1",
                    "title": "Work package 1",
                    "children": [
                        {
                            "id": "caf61803-70e5-4ac3-9adb-53a35f65a2f3",
                            "code": "TASK1",
                            "title": "Task 1",
                        }
                    ]
                },
                {
                    "id": "caf61803-70e5-4ac3-9adb-53a35f65a2f4",
                    "code": "WP2",
                    "title": "Work package 2",
                    "children": []
                }
            ]
        })

        # test synchronization
        ProjectService.synchronize_space_project(space_project)

        all_projects_count = Project.select().count()

        # test get
        project: Project = Project.get_by_id_and_check("caf61803-70e5-4ac3-9adb-53a35f65a2f1")

        json_ = project.to_json(deep=True)
        self.assertEqual(json_['code'], 'Root')
        self.assertEqual(len(json_['children']), 2)
        self.assertEqual(json_['children'][0]['code'], 'WP1')
        self.assertEqual(json_['children'][1]['code'], 'WP2')
        self.assertEqual(len(json_['children'][0]['children']), 1)
        self.assertEqual(json_['children'][0]['children'][0]['code'], 'TASK1')
        self.assertEqual(len(json_['children'][0]['children'][0]['children']), 0)
        self.assertEqual(len(json_['children'][1]['children']), 0)

        # test get available projects as tree
        project_trees = ProjectService.get_project_trees()
        # check that the root project was returned but not the children
        self.assertTrue(any(project_tree.code == 'Root' for project_tree in project_trees))
        self.assertFalse(any(project_tree.code == 'WP1' for project_tree in project_trees))

        # Test another synchronization to check that the project is not duplicated
        ProjectService.synchronize_space_project(space_project)
        self.assertEqual(Project.select().count(), all_projects_count)

        # Test deletion
        experiment = ExperimentService.create_empty_experiment('caf61803-70e5-4ac3-9adb-53a35f65a2f3')

        # Should not be able to delete a project with experiments
        with self.assertRaises(Exception):
            ProjectService.delete_project(project.id)

        ExperimentService.delete_experiment(experiment.id)
        ProjectService.delete_project(project.id)
        self.assertEqual(Project.select().count(), 0)

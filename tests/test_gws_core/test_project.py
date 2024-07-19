

from typing import List

from gws_core import BaseTestCase
from gws_core.core.utils.date_helper import DateHelper
from gws_core.experiment.experiment import Experiment
from gws_core.experiment.experiment_service import ExperimentService
from gws_core.project.project import Project
from gws_core.project.project_dto import ProjectLevelStatus, SpaceProject
from gws_core.project.project_service import ProjectService


# test_project
class TestProject(BaseTestCase):

    def test_get_or_create_project_with_children(self):

        space_project: SpaceProject = SpaceProject.from_json({
            "id": "caf61803-70e5-4ac3-9adb-53a35f65a2f1",
            "code": "Root",
            "title": "Root project",
            "levelStatus": "PARENT",
            "children": [
                {
                    "id": "caf61803-70e5-4ac3-9adb-53a35f65a2f2",
                    "code": "WP1",
                    "title": "Work package 1",
                    "levelStatus": "PARENT",
                    "children": [
                        {
                            "id": "caf61803-70e5-4ac3-9adb-53a35f65a2f3",
                            "code": "TASK1",
                            "title": "Task 1",
                            "levelStatus": "LEAF",
                        }
                    ]
                },
                {
                    "id": "caf61803-70e5-4ac3-9adb-53a35f65a2f4",
                    "code": "WP2",
                    "title": "Work package 2",
                    "levelStatus": "PARENT",
                    "children": []
                }
            ]
        })

        # test synchronization
        ProjectService.synchronize_space_project(space_project)

        all_projects_count = Project.select().count()

        # test get
        project: Project = Project.get_by_id_and_check("caf61803-70e5-4ac3-9adb-53a35f65a2f1")

        json_ = project.to_tree_dto()
        self.assertEqual(json_.code, 'Root')
        self.assertEqual(len(json_.children), 2)
        self.assertEqual(json_.children[0].code, 'WP1')
        self.assertEqual(json_.children[1].code, 'WP2')
        self.assertEqual(len(json_.children[0].children), 1)
        self.assertEqual(json_.children[0].children[0].code, 'TASK1')
        self.assertEqual(len(json_.children[0].children[0].children), 0)
        self.assertEqual(len(json_.children[1].children), 0)

        # test get available projects as tree
        project_trees = ProjectService.get_project_trees()
        # check that the root project was returned but not the children
        self.assertTrue(any(project_tree.code == 'Root' for project_tree in project_trees))
        self.assertFalse(any(project_tree.code == 'WP1' for project_tree in project_trees))

        # Test another synchronization to delete the WP2 project and verify that the other project were not changed
        space_project.children = space_project.children[:1]
        ProjectService.synchronize_space_project(space_project)
        self.assertEqual(Project.select().count(), all_projects_count - 1)

        # test get
        project: Project = Project.get_by_id_and_check("caf61803-70e5-4ac3-9adb-53a35f65a2f1")
        self.assertEqual(project.code, 'Root')
        self.assertEqual(len(project.children), 1)
        self.assertEqual(project.children[0].code, 'WP1')

        # Test deletion, create a sync experiment
        experiment: Experiment = ExperimentService.create_experiment(project_id='caf61803-70e5-4ac3-9adb-53a35f65a2f3')
        experiment.last_sync_at = DateHelper.now_utc()
        experiment.last_sync_by = experiment.created_by
        experiment.save()

        # Should not be able to delete a project with experiments
        with self.assertRaises(Exception):
            ProjectService.delete_project(project.id)

        # un-sync the experiment
        experiment.last_sync_at = None
        experiment.last_sync_by = None
        experiment.save()

        # Now we should be able to delete the project
        ProjectService.delete_project(project.id)
        self.assertEqual(Project.select().count(), 0)

        # check that the project was removed from experiment
        experiment = experiment.refresh()
        self.assertIsNone(experiment.project)

    def test_project_sync(self):

        # delete all projects
        Project.delete().execute()

        space_projects: List[SpaceProject] = [
            SpaceProject.from_json({
                "id": "caf61803-70e5-4ac3-9adb-53a35f65a2f1",
                "code": "Root",
                "title": "Root project",
                "levelStatus": "PARENT",
                "children": [
                    {
                        "id": "caf61803-70e5-4ac3-9adb-53a35f65a2f2",
                        "code": "WP1",
                        "title": "Work package 1",
                        "levelStatus": "LEAF",
                    },
                    {
                        "id": "caf61803-70e5-4ac3-9adb-53a35f65a2f4",
                        "code": "WP2",
                        "title": "Work package 2",
                        "levelStatus": "LEAF",
                    }
                ]
            }),
            SpaceProject.from_json({
                "id": "caf61803-70e5-4ac3-9adb-53a35f65a2f5",
                "code": "Root 2",
                "title": "Root project 2",
                "levelStatus": "LEAF",
            }),
        ]

        ProjectService.synchronize_projects(space_projects)

        self.assertEqual(Project.select().count(), 4)
        root_1 = Project.get_by_id_and_check("caf61803-70e5-4ac3-9adb-53a35f65a2f1")
        self.assertEqual(root_1.code, 'Root')
        self.assertEqual(root_1.level_status, ProjectLevelStatus.PARENT)
        self.assertEqual(len(root_1.children), 2)
        self.assertEqual(root_1.children[0].id, 'caf61803-70e5-4ac3-9adb-53a35f65a2f2')
        self.assertEqual(root_1.children[0].code, 'WP1')
        self.assertEqual(root_1.children[0].level_status, ProjectLevelStatus.LEAF)
        self.assertEqual(root_1.children[1].id, 'caf61803-70e5-4ac3-9adb-53a35f65a2f4')
        self.assertEqual(root_1.children[1].code, 'WP2')
        self.assertEqual(root_1.children[1].level_status, ProjectLevelStatus.LEAF)

        new_projects: List[SpaceProject] = [
            SpaceProject.from_json({
                "id": "caf61803-70e5-4ac3-9adb-53a35f65a2f1",
                "code": "Root new",  # code updated
                "title": "Root project",
                "levelStatus": "PARENT",
                "children": [
                    {
                        "id": "caf61803-70e5-4ac3-9adb-53a35f65a2f2",
                        "code": "WP1 new",  # code updated
                        "title": "Work package 1",
                        "levelStatus": "LEAF",
                    },
                    # child removed
                    # new child
                    {
                        "id": "caf61803-70e5-4ac3-9adb-53a35f65a2f6",
                        "code": "New child",
                        "title": "New child",
                        "levelStatus": "LEAF",
                    }
                ]
            }),
            # root 2 removed
            # new root 3
            SpaceProject.from_json({
                "id": "caf61803-70e5-4ac3-9adb-53a35f65a2f7",
                "code": "Root 3",
                "title": "Root project 3",
                "levelStatus": "LEAF",
            }),
        ]

        ProjectService.synchronize_projects(new_projects)

        self.assertEqual(Project.select().count(), 4)
        new_root_1 = Project.get_by_id_and_check("caf61803-70e5-4ac3-9adb-53a35f65a2f1")
        self.assertEqual(new_root_1.code, 'Root new')
        self.assertEqual(new_root_1.level_status, ProjectLevelStatus.PARENT)
        self.assertEqual(len(new_root_1.children), 2)
        self.assertEqual(new_root_1.children[0].id, 'caf61803-70e5-4ac3-9adb-53a35f65a2f2')
        self.assertEqual(new_root_1.children[0].code, 'WP1 new')
        self.assertEqual(new_root_1.children[0].level_status, ProjectLevelStatus.LEAF)
        self.assertEqual(new_root_1.children[1].id, 'caf61803-70e5-4ac3-9adb-53a35f65a2f6')
        self.assertEqual(new_root_1.children[1].code, 'New child')
        self.assertEqual(new_root_1.children[1].level_status, ProjectLevelStatus.LEAF)

        # check WP2 and root 1 were deleted
        self.assertIsNone(Project.get_by_id("caf61803-70e5-4ac3-9adb-53a35f65a2f4"))
        self.assertIsNone(Project.get_by_id("caf61803-70e5-4ac3-9adb-53a35f65a2f5"))
        # check root 3 was created
        self.assertIsNotNone(Project.get_by_id("caf61803-70e5-4ac3-9adb-53a35f65a2f7"))



from typing import List

from gws_core import BaseTestCase
from gws_core.core.utils.date_helper import DateHelper
from gws_core.experiment.experiment import Experiment
from gws_core.experiment.experiment_service import ExperimentService
from gws_core.folder.space_folder import SpaceFolder
from gws_core.folder.space_folder_dto import ExternalSpaceFolder
from gws_core.folder.space_folder_service import SpaceFolderService


# test_space_folder
class TestFolder(BaseTestCase):

    def test_get_or_create_folder_with_children(self):

        # delete all folders
        SpaceFolder.delete().execute()

        space_folder: ExternalSpaceFolder = ExternalSpaceFolder.from_json({
            "id": "caf61803-70e5-4ac3-9adb-53a35f65a2f1",
            "title": "Root folder",
            "children": [
                {
                    "id": "caf61803-70e5-4ac3-9adb-53a35f65a2f2",
                    "title": "Work package 1",
                    "children": [
                        {
                            "id": "caf61803-70e5-4ac3-9adb-53a35f65a2f3",
                            "title": "Task 1",
                        }
                    ]
                },
                {
                    "id": "caf61803-70e5-4ac3-9adb-53a35f65a2f4",
                    "title": "Work package 2",
                    "children": []
                }
            ]
        })

        # test synchronization
        SpaceFolderService.synchronize_space_folder(space_folder)

        all_folders_count = SpaceFolder.select().count()

        # test get
        folder: SpaceFolder = SpaceFolder.get_by_id_and_check("caf61803-70e5-4ac3-9adb-53a35f65a2f1")

        json_ = folder.to_tree_dto()
        self.assertEqual(json_.title, 'Root folder')
        self.assertEqual(len(json_.children), 2)
        self.assertEqual(json_.children[0].title, 'Work package 1')
        self.assertEqual(json_.children[1].title, 'Work package 2')
        self.assertEqual(len(json_.children[0].children), 1)
        self.assertEqual(json_.children[0].children[0].title, 'Task 1')
        self.assertEqual(len(json_.children[0].children[0].children), 0)
        self.assertEqual(len(json_.children[1].children), 0)

        # test get available folders as tree
        folder_trees = SpaceFolderService.get_folder_trees()
        # check that the root folder was returned but not the children
        self.assertTrue(any(folder_tree.title == 'Root folder' for folder_tree in folder_trees))
        self.assertFalse(any(folder_tree.title == 'Work package 1' for folder_tree in folder_trees))

        # Test another synchronization to delete the Work package 2 folder and verify that the other folder were not changed
        space_folder.children = space_folder.children[:1]
        SpaceFolderService.synchronize_space_folder(space_folder)
        self.assertEqual(SpaceFolder.select().count(), all_folders_count - 1)

        # test get
        folder = SpaceFolder.get_by_id_and_check("caf61803-70e5-4ac3-9adb-53a35f65a2f1")
        self.assertEqual(folder.title, 'Root folder')
        self.assertEqual(len(folder.children), 1)
        self.assertEqual(folder.children[0].title, 'Work package 1')

        # Test deletion, create a sync experiment
        experiment: Experiment = ExperimentService.create_experiment(folder_id='caf61803-70e5-4ac3-9adb-53a35f65a2f3')
        experiment.last_sync_at = DateHelper.now_utc()
        experiment.last_sync_by = experiment.created_by
        experiment.save()

        # Should not be able to delete a folder with experiments
        with self.assertRaises(Exception):
            SpaceFolderService.delete_folder(folder.id)

        # un-sync the experiment
        experiment.last_sync_at = None
        experiment.last_sync_by = None
        experiment.save()

        # Now we should be able to delete the folder
        SpaceFolderService.delete_folder(folder.id)
        self.assertEqual(SpaceFolder.select().count(), 0)

        # check that the folder was removed from experiment
        experiment = experiment.refresh()
        self.assertIsNone(experiment.folder)

    def test_folder_sync(self):

        # delete all folders
        SpaceFolder.delete().execute()

        space_folders: List[ExternalSpaceFolder] = [
            ExternalSpaceFolder.from_json({
                "id": "caf61803-70e5-4ac3-9adb-53a35f65a2f1",
                "title": "Root folder",
                "children": [
                    {
                        "id": "caf61803-70e5-4ac3-9adb-53a35f65a2f2",
                        "title": "Work package 1",
                    },
                    {
                        "id": "caf61803-70e5-4ac3-9adb-53a35f65a2f4",
                        "title": "Work package 2",
                    }
                ]
            }),
            ExternalSpaceFolder.from_json({
                "id": "caf61803-70e5-4ac3-9adb-53a35f65a2f5",
                "title": "Root folder 2",
            }),
        ]

        SpaceFolderService.synchronize_folders(space_folders)

        self.assertEqual(SpaceFolder.select().count(), 4)
        root_1 = SpaceFolder.get_by_id_and_check("caf61803-70e5-4ac3-9adb-53a35f65a2f1")
        self.assertEqual(root_1.title, 'Root folder')
        self.assertEqual(len(root_1.children), 2)
        self.assertEqual(root_1.children[0].id, 'caf61803-70e5-4ac3-9adb-53a35f65a2f2')
        self.assertEqual(root_1.children[0].title, 'Work package 1')
        self.assertEqual(root_1.children[1].id, 'caf61803-70e5-4ac3-9adb-53a35f65a2f4')
        self.assertEqual(root_1.children[1].title, 'Work package 2')

        new_folders: List[ExternalSpaceFolder] = [
            ExternalSpaceFolder.from_json({
                "id": "caf61803-70e5-4ac3-9adb-53a35f65a2f1",
                "title": "Root new",  # title updated
                "children": [
                    {
                        "id": "caf61803-70e5-4ac3-9adb-53a35f65a2f2",
                        "title": "Work package 1 new",  # title updated
                    },
                    # child removed
                    # new child
                    {
                        "id": "caf61803-70e5-4ac3-9adb-53a35f65a2f6",
                        "title": "New child",
                    }
                ]
            }),
            # root 2 removed
            # new root 3
            ExternalSpaceFolder.from_json({
                "id": "caf61803-70e5-4ac3-9adb-53a35f65a2f7",
                "title": "Root folder 3",
            }),
        ]

        SpaceFolderService.synchronize_folders(new_folders)

        self.assertEqual(SpaceFolder.select().count(), 4)
        new_root_1 = SpaceFolder.get_by_id_and_check("caf61803-70e5-4ac3-9adb-53a35f65a2f1")
        self.assertEqual(new_root_1.title, 'Root new')
        self.assertEqual(len(new_root_1.children), 2)
        self.assertEqual(new_root_1.children[0].id, 'caf61803-70e5-4ac3-9adb-53a35f65a2f2')
        self.assertEqual(new_root_1.children[0].title, 'Work package 1 new')
        self.assertEqual(new_root_1.children[1].id, 'caf61803-70e5-4ac3-9adb-53a35f65a2f6')
        self.assertEqual(new_root_1.children[1].title, 'New child')

        # check Work package 2 and root 1 were deleted
        self.assertIsNone(SpaceFolder.get_by_id("caf61803-70e5-4ac3-9adb-53a35f65a2f4"))
        self.assertIsNone(SpaceFolder.get_by_id("caf61803-70e5-4ac3-9adb-53a35f65a2f5"))
        # check root 3 was created
        self.assertIsNotNone(SpaceFolder.get_by_id("caf61803-70e5-4ac3-9adb-53a35f65a2f7"))
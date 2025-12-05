import os

from gws_core.core.utils.settings import Settings
from gws_core.impl.file.create_folder_from_files import CreateFolderFromFiles
from gws_core.impl.file.file import File
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.file.folder import Folder
from gws_core.impl.file.fs_node import FSNode
from gws_core.io.dynamic_io import DynamicInputs
from gws_core.io.io_spec import InputSpec
from gws_core.task.task_runner import TaskRunner
from gws_core.test.base_test_case_light import BaseTestCaseLight


# test_create_folder_from_file
class TestCreateFolderFromFile(BaseTestCaseLight):
    def test_create_folder_from_file(self):
        temp_dir = Settings.make_temp_dir()

        file_1_path = FileHelper.create_empty_file_if_not_exist(
            os.path.join(temp_dir, "test_file.txt")
        )
        # write some content to the file
        with open(file_1_path, "w", encoding="UTF-8") as f:
            f.write("Hello")

        folder_1_path = FileHelper.create_dir_if_not_exist(os.path.join(temp_dir, "test_folder"))
        # create a file in the folder
        FileHelper.create_empty_file_if_not_exist(os.path.join(folder_1_path, "sub_file.txt"))

        file = File(str(file_1_path))
        folder = Folder(str(folder_1_path))

        task_runner = TaskRunner(
            CreateFolderFromFiles,
            params={
                "folder_name": "new_folder",
                "filenames": [
                    {"filename": ""},
                    {"filename": "new_folder"},
                ],
            },
            inputs={"resource_1": file, "resource_2": folder},
            input_specs=DynamicInputs(
                {
                    "resource_1": InputSpec(FSNode),
                    "resource_2": InputSpec(FSNode),
                }
            ),
        )

        outputs = task_runner.run()

        folder_result: Folder = outputs.get("folder")

        self.assertEqual(folder_result.get_base_name(), "new_folder")

        self.assertIsInstance(folder_result, Folder)
        self.assertTrue(FileHelper.exists_on_os(folder_result.path))
        self.assertTrue(FileHelper.exists_on_os(os.path.join(folder_result.path, "test_file.txt")))

        # check file content
        with open(os.path.join(folder_result.path, "test_file.txt"), encoding="UTF-8") as f:
            self.assertEqual(f.read(), "Hello")

        # check that the folder has been created
        self.assertTrue(FileHelper.exists_on_os(os.path.join(folder_result.path, "new_folder")))
        self.assertTrue(
            FileHelper.exists_on_os(os.path.join(folder_result.path, "new_folder", "sub_file.txt"))
        )

        # Check that the original file and folder are still there
        self.assertTrue(FileHelper.exists_on_os(file_1_path))
        self.assertTrue(FileHelper.exists_on_os(folder_1_path))

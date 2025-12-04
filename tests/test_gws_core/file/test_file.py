import os

from gws_core import (
    BaseTestCase,
    ConfigParams,
    File,
    FsNodeService,
    OutputSpec,
    OutputSpecs,
    Task,
    TaskInputs,
    TaskOutputs,
    task_decorator,
)
from gws_core.config.config_specs import ConfigSpecs
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.file.file_store import FileStore
from gws_core.impl.file.local_file_store import LocalFileStore
from gws_core.process.process_proxy import ProcessProxy
from gws_core.resource.resource_model import ResourceModel
from gws_core.scenario.scenario_proxy import ScenarioProxy


@task_decorator("CreateFileTest")
class CreateFileTest(Task):
    """Simple process that create a file anywhere on the server"""

    output_specs = OutputSpecs({"file": OutputSpec(File)})
    config_specs = ConfigSpecs({})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        file = File()
        file.path = os.path.join(Settings.get_instance().get_data_dir(), "test_file.txt")
        file.write("Hello")
        return {"file": file}


# test_file
class TestFile(BaseTestCase):
    def test_file_attr(self):
        tmp_dir = Settings.make_temp_dir()
        temp_file = FileHelper.create_empty_file_if_not_exist(
            os.path.join(tmp_dir, "test_attr.txt")
        )
        file: File = File(temp_file)
        self.assertEqual(file.get_default_name(), "test_attr.txt")
        self.assertEqual(file.get_base_name(), "test_attr.txt")
        self.assertEqual(file.extension, "txt")
        self.assertEqual(file.is_txt(), True)

    def test_file(self):
        temp_dir = Settings.make_temp_dir()
        file_path = os.path.join(temp_dir, "test_file.txt")
        open(file_path, "a", encoding="utf-8").close()

        file_1: File = File(file_path)
        file_model: ResourceModel = FsNodeService.create_fs_node_model(fs_node=file_1)

        self.assertTrue(file_model.is_saved())
        self.assertEqual(file_model.fs_node_model.path, file_1.path)

        file_2: File = file_model.get_resource()
        file_3: File = file_model.get_resource()
        self.assertEqual(file_1, file_2)
        self.assertEqual(file_2, file_3)

        self.assertEqual(file_1.path, file_2.path)
        self.assertEqual(file_2.path, file_3.path)
        self.assertEqual(file_model.fs_node_model.path, file_2.path)
        file_2.write("Hi.\n")
        file_2.write("My name is John")

        text = file_1.read()
        self.assertEqual(text, "Hi.\nMy name is John")

    def test_process_file(self):
        """Test that a generated file of a task is moved to file store and check content"""
        scenario: ScenarioProxy = ScenarioProxy()
        scenario.get_protocol().add_process(CreateFileTest, "create_file")

        scenario.run()

        process: ProcessProxy = scenario.get_protocol().get_process("create_file")
        file: File = process.get_output("file")

        file_store: LocalFileStore = LocalFileStore.get_default_instance()
        self.assertTrue(file_store.node_exists(file))
        self.assertEqual(file.read(), "Hello")

        # Check that the file model is saved and correct
        file_model: ResourceModel = process._process_model.out_port("file").get_resource_model()
        self.assertTrue(file_model.is_saved())
        self.assertEqual(file.path, file_model.fs_node_model.path)

        # Test delete
        file_model.delete_instance()
        self.assertFalse(file_store.node_exists(file))

    def test_file_deleted_manually(self):
        """Test a specific case where a file already saved in the store was deleted manually
        When trying to create a new file with the same path, the file should be created
        and the old file resource should be mark as content deleted
        """

        # create a file in the store
        temp_dir = Settings.make_temp_dir()
        file_name = "to_delete.txt"
        file_path = str(
            FileHelper.create_empty_file_if_not_exist(os.path.join(temp_dir, file_name))
        )
        resource_to_delete = FsNodeService.create_fs_node_model(File(file_path))

        file_store: FileStore = LocalFileStore.get_default_instance()
        self.assertTrue(file_store.node_path_exists(resource_to_delete.fs_node_model.path))

        # delete the file manually
        file_store.delete_node_path(resource_to_delete.fs_node_model.path)
        self.assertFalse(file_store.node_path_exists(resource_to_delete.fs_node_model.path))

        # create a new file with the same path
        new_file = str(FileHelper.create_empty_file_if_not_exist(os.path.join(temp_dir, file_name)))
        new_resource = FsNodeService.create_fs_node_model(File(new_file))

        # new file should be in the store
        self.assertTrue(file_store.node_path_exists(new_resource.fs_node_model.path))

        # old resource should be marked as content deleted
        resource_to_delete = resource_to_delete.refresh()
        self.assertTrue(resource_to_delete.content_is_deleted, True)
        self.assertIsNone(resource_to_delete.fs_node_model)

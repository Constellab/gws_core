

import json
import os

from gws_core import (BaseTestCase, ConfigParams, File, FsNodeService,
                      OutputSpec, OutputSpecs, Task, TaskInputs, TaskOutputs,
                      WriteToJsonFile, task_decorator)
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file_store import FileStore
from gws_core.impl.file.local_file_store import LocalFileStore
from gws_core.impl.robot.robot_resource import Robot
from gws_core.impl.robot.robot_tasks import RobotCreate
from gws_core.process.process_proxy import ProcessProxy
from gws_core.protocol.protocol_proxy import ProtocolProxy
from gws_core.resource.resource_model import ResourceModel
from gws_core.scenario.scenario_proxy import ScenarioProxy
from gws_core.task.task_proxy import TaskProxy


@task_decorator("CreateFileTest")
class CreateFileTest(Task):
    """ Simple process that create a file anywhere on the server
    """
    output_specs = OutputSpecs({'file': OutputSpec(File)})
    config_specs = {}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        file = File()
        file.path = os.path.join(Settings.get_instance().get_data_dir(), 'test_file.txt')
        file.write('Hello')
        return {'file': file}


# test_file
class TestFile(BaseTestCase):

    def test_file_attr(self):
        file: File = LocalFileStore.get_default_instance().create_empty_file("test_attr.txt")
        self.assertEqual(file.get_default_name(), "test_attr.txt")
        self.assertEqual(file.extension, "txt")
        self.assertEqual(file.is_txt(), True)

    def test_file(self):
        file_1: File = LocalFileStore.get_default_instance().create_empty_file("my_file.txt")
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
        """Test that a generated file of a task is moved to file store and check content
        """
        scenario: ScenarioProxy = ScenarioProxy()
        scenario.get_protocol().add_process(CreateFileTest, 'create_file')

        scenario.run()

        process: ProcessProxy = scenario.get_protocol().get_process('create_file')
        file: File = process.get_output('file')

        file_store: LocalFileStore = LocalFileStore.get_default_instance()
        self.assertTrue(file_store.node_exists(file))
        self.assertEqual(file.read(), 'Hello')

        # Check that the file model is saved and correct
        file_model: ResourceModel = process._process_model.out_port('file').get_resource_model()
        self.assertTrue(file_model.is_saved())
        self.assertEqual(file.path, file_model.fs_node_model.path)

        # Test delete
        file_model.delete_instance()
        self.assertFalse(file_store.node_exists(file))

    def test_write_to_json_file_process(self):
        """Test a protocol that generate a file
        """
        file_store: FileStore = LocalFileStore.get_default_instance()

        # Chekc that the file doesn't exist at the beginning
        self.assertFalse(file_store.node_name_exists('robot.json'))

        scenario: ScenarioProxy = ScenarioProxy()
        protocol: ProtocolProxy = scenario.get_protocol()
        create: TaskProxy = protocol.add_process(RobotCreate, 'create')
        write: TaskProxy = protocol.add_process(WriteToJsonFile, 'write', {'filename': 'robot'})
        protocol.add_connectors([
            (create >> 'robot', write << 'resource'),
        ])

        scenario.run()

        # refresh the create
        create.refresh()
        write.refresh()
        robot: Robot = create.get_output('robot')
        file_model: ResourceModel = write._process_model.out_port('file').get_resource_model()

        # check that the file model is create and valid
        self.assertIsNotNone(file_model.id)

        file: File = file_model.get_resource()
        # check that the file was created
        self.assertTrue(file_store.node_name_exists(file.get_default_name()))

        # Check file content
        content: str = file.read()
        params = ConfigParams()
        self.assert_json(json.loads(content), robot.view_as_json(params).to_dto(params).to_json_dict())

        # Check file size
        self.assertTrue(file_model.fs_node_model.size > 0)

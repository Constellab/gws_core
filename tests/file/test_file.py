# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import os

from gws_core import (BaseTestCase, ConfigParams, File, FileModel, FileService,
                      GTest, LocalFileStore, Robot, RobotCreate, Task,
                      TaskInputs, TaskOutputs, WriteToJsonFile, task_decorator)
from gws_core.core.utils.settings import Settings
from gws_core.experiment.experiment_interface import IExperiment
from gws_core.impl.file.file_store import FileStore
from gws_core.process.process_interface import IProcess
from gws_core.protocol.protocol_interface import IProtocol
from gws_core.task.task_interface import ITask


@task_decorator("CreateFileTest")
class CreateFileTest(Task):
    """ Simple process that create a file anywhere on the server
    """
    input_specs = {}
    output_specs = {'file': File}
    config_specs = {}

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        file = File()
        file.path = os.path.join(Settings.retrieve().get_data_dir(), 'test_file.txt')
        file.write('Hello')
        return {'file': file}


class TestFile(BaseTestCase):

    def test_file(self):
        GTest.print("File")

        file_1: File = LocalFileStore.get_default_instance().create_empty("my_file.txt")
        file_model: FileModel = FileService.create_file_model(file=file_1)

        self.assertTrue(file_model.is_saved())
        self.assertEqual(file_model.path, file_1.path)

        file_2: File = file_model.get_resource()
        file_3: File = file_model.get_resource()
        self.assertEqual(file_1, file_2)
        self.assertEqual(file_2, file_3)

        self.assertEqual(file_1.path, file_2.path)
        self.assertEqual(file_2.path, file_3.path)
        self.assertEqual(file_model.path, file_2.path)
        file_2.write("Hi.\n")
        file_2.write("My name is John")

        text = file_1.read()
        self.assertEqual(text, "Hi.\nMy name is John")
        self.assertTrue(file_model.verify_hash())

    async def test__process_file(self):
        """Test that a generated file of a task is moved to file store and check content
        """
        experiment: IExperiment = IExperiment()
        process: IProcess = experiment.get_protocol().add_process(CreateFileTest, 'create_file')

        await experiment.run()

        file: File = process.get_output('file')

        file_store: LocalFileStore = LocalFileStore.get_default_instance()
        self.assertTrue(file_store.file_exists(file))
        self.assertEqual(file.read(), 'Hello')

        # Check that the file model is saved and correct
        file_model: FileModel = process._process_model.out_port('file').resource_model
        self.assertTrue(file_model.is_saved())
        self.assertEqual(file.path, file_model.path)

    async def test_write_to_json_file_process(self):
        """Test a protocol that generate a file
        """
        file_store: FileStore = LocalFileStore.get_default_instance()

        # Chekc that the file doesn't exist at the beginning
        self.assertFalse(file_store.file_name_exists('robot.json'))

        experiment: IExperiment = IExperiment()
        protocol: IProtocol = experiment.get_protocol()
        create: ITask = protocol.add_process(RobotCreate, 'create')
        write: ITask = protocol.add_process(WriteToJsonFile, 'write', {'filename': 'robot'})
        protocol.add_connectors([
            (create >> 'robot', write << 'resource'),
        ])

        await experiment.run()

        robot: Robot = create.get_output('robot')
        file_model: FileModel = write._task_model.out_port('file').resource_model

        # check that the file model is create and valid
        self.assertIsNotNone(file_model.id)
        self.assertTrue(isinstance(file_model, FileModel))

        file: File = file_model.get_resource()
        # check that the file was created
        self.assertTrue(file_store.file_name_exists(file.name))

        # Check file content
        content: str = file.read()
        self.assertEqual(content, json.dumps(robot.view_as_dict().to_dict()))

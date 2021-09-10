# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json

from gws_core import (BaseTestCase, ConfigParams, Experiment,
                      ExperimentService, File, FileModel, FileService, GTest,
                      LocalFileStore, ProcessableFactory, ProcessableSpec,
                      ProcessModel, Protocol, ProtocolModel, Robot,
                      RobotCreate, WriteToJsonFile, protocol_decorator)
from gws_core.impl.file.file_store import FileStore


@protocol_decorator("RobotToFile")
class RobotToFile(Protocol):
    def configure_protocol(self, config_params: ConfigParams) -> None:
        create: ProcessableSpec = self.add_process(RobotCreate, 'create')
        write: ProcessableSpec = self.add_process(WriteToJsonFile, 'write').configure('filename', 'robot')

        self.add_connectors([
            (create >> 'robot', write << 'resource'),
        ])


class TestFile(BaseTestCase):

    def test_file(self):
        GTest.print("File")

        file_store: LocalFileStore = LocalFileStore()
        file_1: File = file_store.create_file("my_file.txt")
        file_model: FileModel = FileService.create_file_model(file=file_1)

        self.assertTrue(file_model.is_saved())
        self.assertEqual(file_model.path, file_1.path)

        file_2: File = file_model.get_resource()
        file_3: File = file_model.get_resource()
        self.assertNotEqual(file_1, file_2)
        self.assertEqual(file_2, file_3)  # use cached data

        self.assertEqual(file_1.path, file_2.path)
        self.assertEqual(file_2.path, file_3.path)
        self.assertEqual(file_model.path, file_2.path)
        file_2.write("Hi.\n")
        file_2.write("My name is John")

        text = file_1.read()
        self.assertEqual(text, "Hi.\nMy name is John")
        self.assertTrue(file_model.verify_hash())

    async def test_file_process(self):
        """Test a protocol that generate a file
        """
        file_store: FileStore = LocalFileStore.get_default_instance()

        # Chekc that the file doesn't exist at the beginning
        self.assertFalse(file_store.file_exists('robot.json'))

        protocol: ProtocolModel = ProcessableFactory.create_protocol_model_from_type(RobotToFile)

        experiment: Experiment = ExperimentService.create_experiment_from_protocol_model(protocol)
        experiment = await ExperimentService.run_experiment(experiment)

        create: ProcessModel = experiment.protocol.get_process('create')
        write: ProcessModel = experiment.protocol.get_process('write')

        robot: Robot = create.out_port('robot').get_resource()
        file_model: FileModel = write.out_port('file').resource_model

        # check that the file model is create and valid
        self.assertIsNotNone(file_model.id)
        self.assertTrue(isinstance(file_model, FileModel))

        file: File = file_model.get_resource()
        # check that the file was created
        self.assertTrue(file_store.file_exists(file.name))

        # Check file content
        content: str = file.read()
        self.assertEqual(content, json.dumps(robot.to_json()))

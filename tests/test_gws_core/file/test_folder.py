

import os

from gws_core import (BaseTestCase, ConfigParams, FileHelper, Folder,
                      IExperiment, OutputSpec, OutputSpecs, Settings, Task,
                      TaskInputs, TaskOutputs, task_decorator)
from gws_core.impl.file.file import File
from gws_core.impl.file.folder_task import FolderExporter
from gws_core.impl.file.local_file_store import LocalFileStore
from gws_core.impl.text.text_view import SimpleTextView
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_model import ResourceModel
from gws_core.task.converter.converter_service import ConverterService
from gws_core.task.task_runner import TaskRunner


@task_decorator("CreateFolderTest")
class CreateFolderTest(Task):
    """ Simple process that create a file anywhere on the server
    """
    output_specs = OutputSpecs({'folder': OutputSpec(Folder)})
    config_specs = {}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        folder = Folder()
        folder.path = os.path.join(
            Settings.get_instance().get_data_dir(), 'test_folder')
        FileHelper.create_dir_if_not_exist(folder.path)
        return {'folder': folder}


# test_folder
class TestFolder(BaseTestCase):

    def test_folder_attr(self):
        folder: Folder = LocalFileStore.get_default_instance().create_empty_folder("folder")
        self.assertEqual(folder.get_default_name(), "folder")

        sub_file = folder.create_empty_file_if_not_exist('test.txt')
        # write test to sub file
        open(sub_file, 'w', encoding='UTF-8').write('test')
        folder.create_dir_if_not_exist('sub_dir')

        list_ = folder.list_dir()
        list_.sort()
        self.assertEqual(list_, ['sub_dir', 'test.txt'])
        self.assertTrue(folder.has_node('test.txt'))
        self.assertTrue(folder.has_node('sub_dir'))

        # Test json view
        params = ConfigParams()
        vw = folder.view_as_json(params)
        view_dto = vw.to_dto(params)
        self.assertIsNotNone(view_dto.data)

        # Test sub file view
        result: SimpleTextView = folder.view_sub_file(
            ConfigParams({'sub_file_path': 'test.txt'}))
        self.assertTrue(isinstance(result, SimpleTextView))
        self.assertEqual(result._data.text, 'test')

        # Test creating a sub file and sub folder directly
        sub_file_2 = folder.create_dir_if_not_exist('sub_folder/test.txt')
        sub_folder_2 = folder.create_empty_file_if_not_exist('sub_folder2/test.txt')
        self.assertTrue(folder.has_node('sub_folder/test.txt'))
        self.assertTrue(folder.has_node('sub_folder2/test.txt'))

    def test_folder_process(self):
        experiment: IExperiment = IExperiment()
        experiment.get_protocol().add_process(CreateFolderTest, 'create_folder')

        experiment.run()

        process = experiment.get_protocol().get_process('create_folder')
        folder: Folder = process.get_output('folder')

        file_store: LocalFileStore = LocalFileStore.get_default_instance()
        self.assertTrue(file_store.node_exists(folder))

        # Check that the file model is saved and correct
        file_model: ResourceModel = process._process_model.out_port(
            'folder').resource_model
        self.assertTrue(file_model.is_saved())
        self.assertEqual(folder.path, file_model.fs_node_model.path)

    def test_file_extractor(self):
        temp = Settings.make_temp_dir()
        folder: Folder = Folder(temp)

        sub_file_path = folder.create_empty_file_if_not_exist('test.txt')

        # write test to sub file
        open(sub_file_path, 'w', encoding='UTF-8').write('test')

        # save folder
        folder_model = ResourceModel.save_from_resource(
            folder, origin=ResourceOrigin.UPLOADED)

        # Call extractor
        sub_file_model: ResourceModel = ConverterService.call_file_extractor(folder_model_id=folder_model.id,
                                                                             sub_path='test.txt',
                                                                             fs_node_typing_name=File._typing_name)

        # Check that the file was extracted from folder
        self.assertEqual(sub_file_model.fs_node_model.is_symbolic_link, True)
        self.assertEqual(os.path.join(folder_model.fs_node_model.path, 'test.txt'),
                         sub_file_model.fs_node_model.path)

        sub_file: File = sub_file_model.get_resource()
        self.assertTrue(isinstance(sub_file, File))
        self.assertEqual(sub_file.read(), 'test')

    def test_folder_exporter(self):
        temp = Settings.make_temp_dir()
        folder: Folder = Folder(temp)
        sub_file_path = folder.create_empty_file_if_not_exist('test.txt')
        # write test to sub file
        open(sub_file_path, 'w', encoding='UTF-8').write('test')

        # Call exporter to zip
        task_runner = TaskRunner(FolderExporter, inputs={'source': folder})
        result = task_runner.run()
        target: File = result['target']
        self.assertTrue(isinstance(target, File))
        self.assertEqual(target.extension, 'zip')

        # Call exporter to tar.gz
        task_runner = TaskRunner(FolderExporter, inputs={'source': folder}, params={'compression': 'tar.gz'})
        result = task_runner.run()
        target: File = result['target']
        self.assertTrue(isinstance(target, File))
        self.assertEqual(target.extension, 'gz')

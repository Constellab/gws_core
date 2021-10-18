
import os

from gws_core import (BaseTestCase, ConfigParams, FileHelper, Folder,
                      FSNodeModel, IExperiment, IProcess, LocalFileStore,
                      Settings, Task, TaskInputs, TaskOutputs, task_decorator)


@task_decorator("CreateFolderTest")
class CreateFolderTest(Task):
    """ Simple process that create a file anywhere on the server
    """
    input_specs = {}
    output_specs = {'folder': Folder}
    config_specs = {}

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        folder = Folder()
        folder.path = os.path.join(Settings.retrieve().get_data_dir(), 'test_folder')
        FileHelper.create_dir_if_not_exist(folder.path)
        return {'folder': folder}


class TestFolder(BaseTestCase):

    def test_folder_attr(self):
        folder: Folder = LocalFileStore.get_default_instance().create_empty_folder("folder")
        self.assertEqual(folder.name, "folder")

        folder.create_empty_file_if_not_exist('test.txt')
        folder.create_dir_if_not_exist('sub_dir')

        self.assertEqual(folder.list_dir(), ['sub_dir', 'test.txt'])
        self.assertTrue(folder.has_node('test.txt'))
        self.assertTrue(folder.has_node('sub_dir'))

    async def test_folder_process(self):
        experiment: IExperiment = IExperiment()
        process: IProcess = experiment.get_protocol().add_process(CreateFolderTest, 'create_folder')

        await experiment.run()

        folder: Folder = process.get_output('folder')

        file_store: LocalFileStore = LocalFileStore.get_default_instance()
        self.assertTrue(file_store.node_exists(folder))

        # Check that the file model is saved and correct
        file_model: FSNodeModel = process._process_model.out_port('folder').resource_model
        self.assertTrue(file_model.is_saved())
        self.assertEqual(folder.path, file_model.path)

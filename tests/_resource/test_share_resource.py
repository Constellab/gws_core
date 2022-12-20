# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from pandas import DataFrame

from gws_core import (BaseTestCase, ConfigParams, File, IExperiment,
                      OutputSpec, ResourceModel, ResourceSet, Settings, Table,
                      Task, TaskInputs, TaskOutputs, task_decorator)
from gws_core.resource.resource_model import ResourceOrigin
from gws_core.resource.resource_service import ResourceService
from gws_core.share.share_service import ShareService
from gws_core.share.shared_resource import SharedResource
from gws_core.user.current_user_service import CurrentUserService


def get_table() -> Table:
    df = DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    return Table(df)


def get_file() -> File:
    dir = Settings.get_instance().make_temp_dir()
    file_path = os.path.join(dir, 'test.txt')
    with open(file_path, 'w', encoding='UTF-8') as f:
        f.write('test')
    return File(file_path)


@task_decorator(unique_name='GenerateResourceSet')
class GenerateResourceSet(Task):

    input_specs = {}
    output_specs = {
        'resource_set': OutputSpec(ResourceSet)
    }

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        # create a simple resource
        table = get_table()

        # save the resource model
        file = get_file()

        resource_set: ResourceSet = ResourceSet()
        resource_set.add_resource(table, 'table')
        resource_set.add_resource(file, 'file')

        return {'resource_set': resource_set}


# test_share_resource
class TestShareResource(BaseTestCase):

    def test_share_basic_resource(self):

        # create a simple resource
        table = get_table()
        table.name = 'MyTestName'
        table.set_all_column_tags([{'name': 'tag1'}, {'name': 'tag2'}])

        # save the resource model
        original_resource_model = ResourceModel.save_from_resource(table, origin=ResourceOrigin.UPLOADED)

        zip_path = ShareService.download_resource(
            original_resource_model.id, CurrentUserService.get_and_check_current_user())

        resource_unzipper = ShareService.copy_resource_from_zip_2(zip_path)
        new_resource_model: ResourceModel = resource_unzipper.resource_models[0].refresh()

        self.assertNotEqual(original_resource_model.id, new_resource_model.id)
        self.assertNotEqual(original_resource_model.kv_store_path, new_resource_model.kv_store_path)
        self.assertEqual(new_resource_model.name, 'MyTestName')

        new_table: Table = new_resource_model.get_resource()
        self.assertIsInstance(new_table, Table)
        self.assertTrue(table.equals(new_table))

        # test that the origin of the resource exist
        shared_resource: SharedResource = ResourceService.get_shared_resource_origin_info(new_resource_model.id)
        self.assertEqual(shared_resource.resource.id, new_resource_model.id)

    def test_share_file_resource(self):
        # save the resource model
        file = get_file()

        original_resource_model = ResourceModel.save_from_resource(file, origin=ResourceOrigin.UPLOADED)

        zip_path = ShareService.download_resource(
            original_resource_model.id, CurrentUserService.get_and_check_current_user())

        resource_unzipper = ShareService.copy_resource_from_zip_2(zip_path)
        new_resource_model: ResourceModel = resource_unzipper.resource_models[0].refresh()

        self.assertNotEqual(original_resource_model.id, new_resource_model.id)

        new_resource_model = ResourceService.get_resource_by_id(new_resource_model.id)
        self.assertEqual(new_resource_model.name, 'test.txt')
        # check that the fsnode model exist and the path is different that the original one
        # because a new fsnode is created
        self.assertIsNotNone(new_resource_model.fs_node_model)
        self.assertNotEqual(new_resource_model.fs_node_model.path, original_resource_model.fs_node_model.path)

        resource: File = new_resource_model.get_resource()
        self.assertEqual(resource.path, new_resource_model.fs_node_model.path)
        self.assertEqual('test', resource.read())

    async def test_share_resource_set(self):
        i_experiment: IExperiment = IExperiment()
        i_process = i_experiment.get_protocol().add_process(GenerateResourceSet, 'generate_resource_set')
        await i_experiment.run()
        resource_model_id = i_process.get_output_resource_model('resource_set').id

        original_resource_model = ResourceService.get_resource_by_id(resource_model_id)
        original_resource_set: ResourceSet = original_resource_model.get_resource()

        zip_path = ShareService.download_resource(
            resource_model_id, CurrentUserService.get_and_check_current_user())

        resource_unzipper = ShareService.copy_resource_from_zip_2(zip_path)

        self.assertEqual(3, len(resource_unzipper.resource_models))
        new_resource_model = resource_unzipper.resource_models[0].refresh()

        # check that this is another resource model
        self.assertNotEqual(original_resource_model.id, new_resource_model.id)

        resource_set: ResourceSet = new_resource_model.get_resource()
        self.assertIsInstance(resource_set, ResourceSet)

        # check the table
        table: Table = resource_set.get_resource('table')
        self.assertIsNotNone(table)
        original_table: Table = original_resource_set.get_resource('table')
        # check that this is a new resource
        self.assertNotEqual(original_table._model_id, table._model_id)
        self.assertTrue(original_table.equals(table))

        # check the file
        file: File = resource_set.get_resource('file')
        self.assertIsNotNone(file)
        self.assertEqual('test', file.read())
        original_file = original_resource_set.get_resource('file')
        # check that this is a new resource
        self.assertNotEqual(original_file._model_id, file._model_id)

        # Check that there is 2 children of the main resource
        children = ResourceService.get_resource_children(new_resource_model.id)
        self.assertEqual(2, len(children))

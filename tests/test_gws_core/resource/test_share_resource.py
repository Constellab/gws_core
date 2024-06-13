

import os
from datetime import datetime, timedelta

from pandas import DataFrame

from gws_core import (BaseTestCase, ConfigParams, File, IExperiment,
                      OutputSpec, OutputSpecs, ResourceModel, ResourceSet,
                      Settings, Table, Task, TaskInputs, TaskOutputs,
                      task_decorator)
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_loader import ResourceLoader
from gws_core.resource.resource_service import ResourceService
from gws_core.resource.resource_set.resource_list import ResourceList
from gws_core.share.share_link_service import ShareLinkService
from gws_core.share.share_service import ShareService
from gws_core.share.shared_dto import (GenerateShareLinkDTO,
                                       ShareEntityInfoReponseDTO,
                                       ShareEntityZippedResponseDTO,
                                       ShareLinkType)
from gws_core.tag.tag import Tag, TagOrigins
from gws_core.tag.tag_dto import TagOriginType
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

    output_specs = OutputSpecs({
        'resource_set': OutputSpec(ResourceSet)
    })

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        # create a simple resource
        table = get_table()

        # save the resource model
        file = get_file()

        resource_set: ResourceSet = ResourceSet()
        resource_set.add_resource(table, 'table')
        resource_set.add_resource(file, 'file')

        return {'resource_set': resource_set}


@task_decorator(unique_name='GenerateResourceList')
class GenerateResourceList(Task):

    output_specs = OutputSpecs({
        'resource_list': OutputSpec(ResourceList)
    })

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        # create a simple resource
        table = get_table()

        # save the resource model
        file = get_file()

        resource_list: ResourceList = ResourceList()
        resource_list.add_resource(table)
        resource_list.add_resource(file)

        return {'resource_list': resource_list}


# test_share_resource
class TestShareResource(BaseTestCase):

    def test_share_basic_resource(self):

        # create a simple resource
        table = get_table()
        table.name = 'MyTestName'
        table.set_all_column_tags([{'name': 'tag1'}, {'name': 'tag2'}])
        table.tags.add_tag(Tag('resource_tag', 'resource_tag_value', origins=TagOrigins(TagOriginType.USER, 'test')))

        # save the resource model
        original_resource_model = ResourceModel.save_from_resource(table, origin=ResourceOrigin.UPLOADED)

        # create a share link
        tomorrow = datetime.now() + timedelta(days=1)
        generate_dto = GenerateShareLinkDTO(entity_id=original_resource_model.id, entity_type=ShareLinkType.RESOURCE,
                                            valid_until=tomorrow)
        share_link = ShareLinkService.generate_share_link(generate_dto)

        # get the share entity info
        share_entity_info: ShareEntityInfoReponseDTO = ShareService.get_share_entity_info(share_link.token)
        self.assertEqual(share_entity_info.entity_type, ShareLinkType.RESOURCE)
        self.assertEqual(share_entity_info.entity_id, original_resource_model.id)
        self.assertIsNotNone(share_entity_info.zip_entity_route)
        # check that there is only one resource
        self.assertTrue(len(share_entity_info.entity_object), 1)

        # Zip the resource
        response: ShareEntityZippedResponseDTO = ShareService.zip_shared_entity(share_link.token)
        self.assertEqual(response.entity_type, ShareLinkType.RESOURCE)
        self.assertEqual(response.entity_id, original_resource_model.id)
        self.assertIsNotNone(response.download_entity_route)
        self.assertIsNotNone(response.zipped_entity_resource_id)

        zipped_resource: ResourceModel = ResourceModel.get_by_id_and_check(response.zipped_entity_resource_id)
        zip_path = zipped_resource.fs_node_model.path

        resource_unzipper: ResourceLoader = ResourceLoader.from_compress_file(zip_path)
        new_table: Table = resource_unzipper.load_resource()
        # new_resource_model: ResourceModel = resource_unzipper.resource_models[0].refresh()

        # new_table: Table = new_resource_model.get_resource()
        self.assertIsInstance(new_table, Table)
        self.assertTrue(table.equals(new_table))
        self.assertEqual(new_table.name, 'MyTestName')
        self.assertTrue(new_table.tags.has_tag(Tag('resource_tag', 'resource_tag_value')))

        # test that the origin of the resource exist
        # shared_resource: SharedResource = ResourceService.get_shared_resource_origin_info(new_resource_model.id)
        # self.assertEqual(shared_resource.entity.id, new_resource_model.id)

    def test_share_file_resource(self):
        # save the resource model
        file = get_file()

        original_resource_model = ResourceModel.save_from_resource(file, origin=ResourceOrigin.UPLOADED)

        zipped_resource = ShareService.run_zip_resource_exp(
            original_resource_model.id, CurrentUserService.get_and_check_current_user())
        zip_path = zipped_resource.fs_node_model.path

        resource_unzipper: ResourceLoader = ResourceLoader.from_compress_file(zip_path)
        resource: File = resource_unzipper.load_resource()

        self.assertEqual(resource.name, 'test.txt')
        # check that the path is different form the original
        self.assertNotEqual(resource.path, original_resource_model.fs_node_model.path)
        self.assertEqual('test', resource.read())

    def test_share_resource_set(self):
        # Generate a resource set
        i_experiment: IExperiment = IExperiment()
        i_experiment.get_protocol().add_process(GenerateResourceSet, 'generate_resource_set')
        i_experiment.run()
        i_process = i_experiment.get_protocol().get_process('generate_resource_set')
        resource_model_id = i_process.get_output_resource_model('resource_set').id

        original_resource_model = ResourceService.get_by_id_and_check(resource_model_id)
        original_resource_set: ResourceSet = original_resource_model.get_resource()

        zipped_resource = ShareService.run_zip_resource_exp(
            resource_model_id, CurrentUserService.get_and_check_current_user())
        zip_path = zipped_resource.fs_node_model.path

        resource_unzipper: ResourceLoader = ResourceLoader.from_compress_file(zip_path)
        resource_set: ResourceSet = resource_unzipper.load_resource()

        self.assertEqual(3, len(resource_unzipper.get_all_generated_resources()))
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

    def test_share_resource_list(self):
        # Generate a resource list
        i_experiment: IExperiment = IExperiment()
        i_experiment.get_protocol().add_process(GenerateResourceList, 'generate_resource_list')
        i_experiment.run()
        i_process = i_experiment.get_protocol().get_process('generate_resource_list')
        resource_model_id = i_process.get_output_resource_model('resource_list').id

        original_resource_model = ResourceService.get_by_id_and_check(resource_model_id)
        original_resource_list: ResourceList = original_resource_model.get_resource()

        zipped_resource = ShareService.run_zip_resource_exp(
            resource_model_id, CurrentUserService.get_and_check_current_user())
        zip_path = zipped_resource.fs_node_model.path

        resource_unzipper: ResourceLoader = ResourceLoader.from_compress_file(zip_path)
        resource_list: ResourceList = resource_unzipper.load_resource()

        self.assertEqual(3, len(resource_unzipper.get_all_generated_resources()))
        self.assertIsInstance(resource_list, ResourceList)

        # check the table
        table: Table = resource_list[0]
        self.assertIsNotNone(table)
        original_table: Table = original_resource_list[0]
        # check that this is a new resource
        self.assertNotEqual(original_table._model_id, table._model_id)
        self.assertTrue(original_table.equals(table))

        # check the file
        file: File = resource_list[1]
        self.assertIsNotNone(file)
        self.assertEqual('test', file.read())
        original_file = original_resource_list[1]
        # check that this is a new resource
        self.assertNotEqual(original_file._model_id, file._model_id)

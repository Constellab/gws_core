# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core import (File, Paginator, Resource, ResourceImporter, Table,
                      TableImporter, importer_decorator)
from gws_core.core.classes.paginator import Paginator
from gws_core.core.classes.search_builder import SearchParams
from gws_core.data_provider.data_provider import DataProvider
from gws_core.model.typing_service import TypingService
from gws_core.resource.resource_model import ResourceModel, ResourceOrigin
from gws_core.task.converter.converter_service import ConverterService
from gws_core.task.task_typing import TaskTyping
from gws_core.test.base_test_case import BaseTestCase


@importer_decorator(unique_name="TestImporterUnsued", target_type=Resource,
                    supported_extensions=['weirdformatfile'])
class TestImporterResource(ResourceImporter):
    pass


class TestImporter(BaseTestCase):

    def test_get_import_specs(self):
        importers: Paginator[TaskTyping] = TypingService.search_importers(File._typing_name, 'weirdformatfile',
                                                                          SearchParams(), 0, 1000)

        self.assertEqual(len(importers.results), 1)
        self.assertTrue(len([x for x in importers.results if x.get_type() == TestImporterResource]) == 1)

        importers = TypingService.search_importers(File._typing_name, 'anotherweirdformatfile',
                                                   SearchParams(), 0, 1000)
        self.assertEqual(len(importers.results), 0)

        # test with ignore extension activated
        search_params = SearchParams(
            filtersCriteria=[{'key': 'importer_ignore_extension', 'value': True, 'operator': 'EQ'}])
        importers = TypingService.search_importers(File._typing_name, 'anotherweirdformatfile',
                                                   search_params, 0, 1000)
        self.assertTrue(len(importers.results) > 0)

    def test_importer(self):
        file = File(path=DataProvider.get_iris_file().path)

        resource_model: ResourceModel = ResourceModel.save_from_resource(file, origin=ResourceOrigin.UPLOADED)

        # import the table file into a Table
        result: ResourceModel = ConverterService.call_importer(resource_model.id, TableImporter._typing_name,  {})

        self.assertEqual(result.origin, ResourceOrigin.IMPORTED)
        table: Table = result.get_resource()
        self.assertIsInstance(table, Table)

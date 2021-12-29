# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import List

from gws_core import Table, TableFile, TableImporter
from gws_core.resource.resource_model import ResourceModel, ResourceOrigin
from gws_core.task.converter.converter_service import (ConverterService,
                                                       ResourceImportersDTO)
from gws_core.test.base_test_case import BaseTestCase
from tests.gws_core_test_helper import GWSCoreTestHelper


class TestImporter(BaseTestCase):

    def test_get_import_specs(self):
        importers: List[ResourceImportersDTO] = ConverterService.get_resource_importers(TableFile._typing_name)

        self.assertTrue(len(importers) > 0)
        # the first importer group must be importers of TableFile
        self.assertEqual(importers[0].resource.get_type(), TableFile)
        self.assertTrue(len([x for x in importers[0].importers if x.get_type() == TableImporter]) == 1)
        # self.assertTrue(len([x for x in importers if x.get_type() == TextImporter]) == 0)

    async def test_importer(self):
        file = TableFile(path=GWSCoreTestHelper.get_test_data_path("data.csv"))

        resource_model: ResourceModel = ResourceModel.save_from_resource(file, origin=ResourceOrigin.IMPORTED)

        # import the table file into a Table
        result: ResourceModel = await ConverterService.call_importer(resource_model.id, TableImporter._typing_name,  {})

        table: Table = result.get_resource()
        self.assertIsInstance(table, Table)

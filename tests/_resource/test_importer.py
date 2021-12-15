

from gws_core.impl.table.table import Table
from gws_core.impl.table.table_file import TableFile
from gws_core.resource.resource_model import ResourceModel, ResourceOrigin
from gws_core.task.converter.converter_service import ConverterService
from gws_core.test.base_test_case import BaseTestCase
from tests.gws_core_test_helper import GwsCoreTestHelper


class TestImporter(BaseTestCase):

    async def test_importer(self):
        file = TableFile(path=GwsCoreTestHelper.get_test_data_path("data.csv"))

        resource_model: ResourceModel = ResourceModel.save_from_resource(file, origin=ResourceOrigin.IMPORTED)

        # import the table file into a Table
        result: ResourceModel = await ConverterService.call_importer(resource_model.id, {})

        table: Table = result.get_resource()
        self.assertIsInstance(table, Table)

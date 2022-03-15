

from gws_core import File
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.json.json_dict import JSONDict
from gws_core.impl.json.json_tasks import JSONExporter
from gws_core.impl.table.table import Table
from gws_core.impl.table.tasks.table_exporter import TableExporter
from gws_core.resource.resource_model import ResourceModel, ResourceOrigin
from gws_core.task.converter.converter_service import ConverterService
from gws_core.task.task_typing import TaskTyping
from gws_core.test.base_test_case import BaseTestCase


class TestExporter(BaseTestCase):

    def test_get_resource_exporter(self):
        task_typing: TaskTyping = ConverterService.get_resource_exporter(Table)

        self.assertEqual(task_typing.get_type(), TableExporter)

    def test_call_exporter(self):
        json_: JSONDict = JSONDict({"hello": "nice"})

        resource_model: ResourceModel = ResourceModel.save_from_resource(json_, origin=ResourceOrigin.UPLOADED)

        result: File = ConverterService.call_exporter_directly(
            resource_model.id, JSONExporter._typing_name, {})

        self.assertTrue(FileHelper.exists_on_os(result.path))
        self.assertEqual(result.read(), '{"hello": "nice"}')

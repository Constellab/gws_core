# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from unittest.async_case import IsolatedAsyncioTestCase

from gws_core_test_helper import GWSCoreTestHelper

from gws_core import MetadataTableExporter, TaskRunner
from gws_core.data_provider.data_provider import DataProvider


# test_table_metadata
class TestTableMetadataExporter(IsolatedAsyncioTestCase):

    async def test_table_metadata_exporter(self):
        # importer
        metatable = GWSCoreTestHelper.get_sample_metadata_table()
        print(metatable)

        # annotation
        tester = TaskRunner(
            task_type=MetadataTableExporter,
            inputs={
                "source": metatable,
            },
            params={"delimiter": "tab"}
        )
        outputs = await tester.run()
        file = outputs["target"]

        expected_file_path = DataProvider.get_test_data_path("sample_metadata.csv")
        with open(expected_file_path, 'r', encoding="utf-8") as fp:
            expected_text = fp.read()

        with open(file.path, 'r', encoding="utf-8") as fp:
            exported_txt = fp.read()

        self.assertEqual(expected_text, exported_txt)

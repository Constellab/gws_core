# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core import BaseTestCase, Table, TableAnnotator, TaskRunner
from gws_core_test_helper import GWSCoreTestHelper


class TestTableAnnotator(BaseTestCase):

    async def test_table_column_annotator(self):
        # importer
        table = GWSCoreTestHelper.get_sample_table()
        metatable = GWSCoreTestHelper.get_sample_metadata_table()
        print(table)

        self.assertTrue(isinstance(table.get_row_tags(), list))
        self.assertTrue(isinstance(table.get_column_tags(), list))
        self.assertEqual(table.get_row_tags(none_if_empty=True), None)
        self.assertEqual(table.get_column_tags(none_if_empty=True), None)

        # annotation
        tester = TaskRunner(
            task_type=TableAnnotator,
            inputs={
                "table": table,
                "metadata_table": metatable,
            }
        )
        outputs = await tester.run()
        annotated_table = outputs["table"]
        expected_row_tags = [{'Gender': 'M', 'Group': '15', 'Age': '15'},
                             {'Gender': 'F', 'Group': '15', 'Age': '15'},
                             {'Gender': 'M', 'Group': '1', 'Age': '18'},
                             {'Gender': 'F', 'Group': '3', 'Age': '15'},
                             {}]

        self.assertEqual(
            annotated_table.get_meta()['row_tags'], expected_row_tags
        )
        self.assertEqual(
            annotated_table.get_row_tags(), expected_row_tags
        )

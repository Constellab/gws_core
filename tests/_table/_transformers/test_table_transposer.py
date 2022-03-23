# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core import (BaseTestCase, Table, TableRowAnnotator, TableTransposer,
                      TaskRunner)
from gws_core_test_helper import GWSCoreTestHelper


class TestTableTransposer(BaseTestCase):

    async def test_table_column_annotator(self):
        # importer
        table = GWSCoreTestHelper.get_sample_table()
        metatable = GWSCoreTestHelper.get_sample_metadata_table()
        # annotation
        tester = TaskRunner(
            task_type=TableRowAnnotator,
            inputs={
                "sample_table": table,
                "metadata_table": metatable,
            }
        )
        outputs = await tester.run()
        annotated_table = outputs["sample_table"]
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
        print(annotated_table)

        # transpose
        tester = TaskRunner(
            task_type=TableTransposer,
            inputs={
                "source": table,
            }
        )
        outputs = await tester.run()
        transposed_table = outputs["target"]
        self.assertTrue(
            transposed_table.get_data().equals(annotated_table.get_data().T)
        )
        self.assertEqual(
            transposed_table.get_row_tags(),
            annotated_table.get_column_tags()
        )
        self.assertEqual(
            transposed_table.get_column_tags(),
            annotated_table.get_row_tags()
        )
        print(transposed_table)

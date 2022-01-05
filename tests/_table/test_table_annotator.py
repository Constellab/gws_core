# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core import BaseTestCase, Table, TableAnnotator, TaskRunner
from gws_core_test_helper import GWSCoreTestHelper


class TestTableAnnotator(BaseTestCase):

    async def test_table_column_annotator(self):
        # importer
        table = GWSCoreTestHelper.get_small_data_table()
        metatable = GWSCoreTestHelper.get_metadata_table()
        print(table)

        # annotation
        tester = TaskRunner(
            task_type=TableAnnotator,
            inputs={
                "table": table,
                "metadata_table": metatable,
            }
        )
        outputs = await tester.run()
        annotated_table = outputs["annotated_table"]
        print(annotated_table)

        self.assertEqual(annotated_table.row_names, table.row_names)
        self.assertEqual(annotated_table.column_names, [
            "Sex:F|Group:15|Age:15",
            "Sex:M|Group:15|Age:15",
            "Sex:F|Group:3|Age:15",
            "Sex:F|Group:15|Age:15"
        ])
        self.assertTrue((annotated_table.get_data().values == table.get_data().values).all())

    async def test_table_row_annotator(self):
        # importer
        table = GWSCoreTestHelper.get_small_data_table()
        table = Table(data=table.get_data().T)
        metatable = GWSCoreTestHelper.get_metadata_table()

        # annotation
        tester = TaskRunner(
            task_type=TableAnnotator,
            params={"axis": "row"},
            inputs={
                "table": table,
                "metadata_table": metatable,
            }
        )
        outputs = await tester.run()
        annotated_table = outputs["annotated_table"]
        print(annotated_table)

        self.assertEqual(annotated_table.column_names, table.column_names)
        self.assertEqual(annotated_table.row_names, [
            "Sex:F|Group:15|Age:15",
            "Sex:M|Group:15|Age:15",
            "Sex:F|Group:3|Age:15",
            "Sex:F|Group:15|Age:15"
        ])
        self.assertTrue((annotated_table.get_data().values == table.get_data().values).all())

# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core import (BaseTestCase, Table, TableAnnotator,
                      TableTagGrouperHelper, TaskRunner)
from gws_core_test_helper import GWSCoreTestHelper


class TestTableAggregatorHelper(BaseTestCase):
    async def test_table_tag_grouper_helper(self):
        table = GWSCoreTestHelper.get_sample_table()
        metatable = GWSCoreTestHelper.get_sample_metadata_table()
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
        annotated_table = outputs["table"]

        # Sort
        # -----------------------
        grouped_table = TableTagGrouperHelper.group_by_row_tags(annotated_table, keys=['Gender'], func="sort")
        self.assertEqual(grouped_table.row_names, ['B', 'D', 'C', 'A', 'Z'])

        grouped_table = TableTagGrouperHelper.group_by_row_tags(annotated_table, keys=['Gender', 'Group'], func="sort")
        self.assertEqual(grouped_table.row_names, ["D", "B", "A", "C", "Z"])

        # Mean
        # -----------------------
        grouped_table = TableTagGrouperHelper.group_by_row_tags(annotated_table, keys=['Gender'], func="mean")
        self.assertEqual(grouped_table.row_names, ["F", "M"])

        selected = annotated_table.select_by_row_tags([{"Gender": "F"}])
        df1 = grouped_table.get_data().iloc[0, :]
        df2 = selected.get_data().mean(axis=0, skipna=True)
        self.assertTrue(df1.equals(df2))

        selected = annotated_table.select_by_row_tags([{"Gender": "M"}])
        df1 = grouped_table.get_data().iloc[1, :]
        df2 = selected.get_data().mean(axis=0, skipna=True)
        self.assertTrue(df1.equals(df2))

        # Median
        # -----------------------
        grouped_table = TableTagGrouperHelper.group_by_row_tags(annotated_table, keys=['Gender'], func="median")
        self.assertEqual(grouped_table.row_names, ["F", "M"])

        selected = annotated_table.select_by_row_tags([{"Gender": "F"}])
        df1 = grouped_table.get_data().iloc[0, :]
        df2 = selected.get_data().median(axis=0, skipna=True)
        self.assertTrue(df1.equals(df2))

        selected = annotated_table.select_by_row_tags([{"Gender": "M"}])
        df1 = grouped_table.get_data().iloc[1, :]
        df2 = selected.get_data().median(axis=0, skipna=True)
        self.assertTrue(df1.equals(df2))

        print(grouped_table)

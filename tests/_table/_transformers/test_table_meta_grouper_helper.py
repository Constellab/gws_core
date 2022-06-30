# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core import (BaseTestCase, Table, TableRowAnnotator,
                      TableTagGrouperHelper, TaskRunner)
from gws_core_test_helper import GWSCoreTestHelper
from pandas import DataFrame


class TestTableAggregatorHelper(BaseTestCase):
    async def test_table_tag_grouper_helper(self):
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
        annotated_table: Table = outputs["sample_table"]

        # Sort
        # -----------------------
        grouped_table = TableTagGrouperHelper.group_by_row_tags(annotated_table, keys=['Gender'], func="sort")
        print(grouped_table.get_row_tags())

        self.assertEqual(grouped_table.get_row_tags()[0]["Gender"], "F")
        self.assertEqual(grouped_table.get_row_tags()[1]["Gender"], "F")
        self.assertEqual(grouped_table.get_row_tags()[2]["Gender"], "M")
        self.assertEqual(grouped_table.get_row_tags()[3]["Gender"], "M")

        grouped_table = TableTagGrouperHelper.group_by_row_tags(annotated_table, keys=['Gender', 'Group'], func="sort")
        self.assertEqual(grouped_table.get_row_tags()[0]["Gender"], "F")
        self.assertEqual(grouped_table.get_row_tags()[1]["Gender"], "F")
        self.assertEqual(grouped_table.get_row_tags()[2]["Gender"], "M")
        self.assertEqual(grouped_table.get_row_tags()[3]["Gender"], "M")

        #self.assertEqual(grouped_table.row_names, ["D", "B", "A", "C", "Z"])

        # Mean
        # -----------------------
        grouped_table = TableTagGrouperHelper.group_by_row_tags(annotated_table, keys=['Gender'], func="mean")
        self.assertEqual(grouped_table.row_names, ["F", "M"])

        selected: Table = annotated_table.select_by_row_tags([{"Gender": "F"}])
        df1: DataFrame = grouped_table.get_data().iloc[0, :]
        df2: DataFrame = selected.get_data().mean(axis=0, skipna=True)
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

        # Sum
        # -----------------------
        grouped_table = TableTagGrouperHelper.group_by_row_tags(annotated_table, keys=['Gender'], func="sum")
        self.assertEqual(grouped_table.row_names, ["F", "M"])

        selected = annotated_table.select_by_row_tags([{"Gender": "F"}])
        df1 = grouped_table.get_data().iloc[0, :]
        df2 = selected.get_data().sum(axis=0, skipna=True)
        self.assertTrue(df1.equals(df2))

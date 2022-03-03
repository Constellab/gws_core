# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core import (BaseTestCase, GTest, Table, TableFilter, TableImporter,
                      TaskRunner)
from gws_core.extra import DataProvider


class TestTableFilter(BaseTestCase):

    async def test_multi_index_table(self):
        file = DataProvider.get_test_data_file("multi_index_data.csv")
        table: Table = TableImporter.call(file, {"header": 0, "index_column": 0})

        # filter columns
        tester = TaskRunner(
            params={
                "axis_name_filter": [
                    {"axis_type": "column", "value": "Age", "use_regexp": True}
                ]
            },
            inputs={"source": table},
            task_type=TableFilter,
        )
        outputs = await tester.run()
        filtered_table: Table = outputs["target"]
        self.assertEqual(filtered_table.column_names, ["Age"])
        self.assertEqual(filtered_table.row_names, ["Luc", "Lea", "Laura", "Leon"])
        print(filtered_table)

        # filter columns and rows
        tester = TaskRunner(
            params={
                "axis_name_filter": [
                    {"axis_type": "column", "value": "Ag.*", "use_regexp": True},
                    {"axis_type": "row", "value": "Luc|Lea", "use_regexp": True}
                ]
            },
            inputs={"source": table},
            task_type=TableFilter,
        )
        outputs = await tester.run()
        filtered_table = outputs["target"]
        self.assertEqual(filtered_table.column_names, ["Age"])
        self.assertEqual(filtered_table.row_names, ["Luc", "Lea"])

        # filter aggregation
        tester = TaskRunner(
            params={
                "aggregation_filter": [
                    {"direction": "horizontal", "function": "var", "comparator": ">=", "value": 50},
                ]
            },
            inputs={"source": table},
            task_type=TableFilter,
        )
        outputs = await tester.run()
        filtered_table = outputs["target"]
        self.assertEqual(filtered_table.row_names, ["Laura", "Leon"])
        self.assertEqual(filtered_table.column_names, ["Age", "Sex", "City", "Weight"])

        # filter numeric data
        tester = TaskRunner(
            params={
                "numeric_data_filter": [
                    {"column_name": "Age|Weight", "comparator": ">=", "value": 30},
                ]
            },
            inputs={"source": table},
            task_type=TableFilter,
        )
        outputs = await tester.run()
        filtered_table = outputs["target"]
        self.assertEqual(filtered_table.row_names, ["Laura", "Leon"])
        self.assertEqual(filtered_table.column_names, ["Age", "Sex", "City", "Weight"])

        # filter str data
        tester = TaskRunner(
            params={
                "text_data_filter": [
                    {"column_name": "Sex", "comparator": "!=", "value": "M"},
                ]
            },
            inputs={"source": table},
            task_type=TableFilter,
        )
        outputs = await tester.run()
        filtered_table = outputs["target"]
        self.assertEqual(filtered_table.row_names, ["Lea", "Laura"])
        self.assertEqual(filtered_table.column_names, ["Age", "Sex", "City", "Weight"])

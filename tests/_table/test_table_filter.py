# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from gws_core import (BaseTestCase, BoolParam, ConfigParams, Experiment,
                      ExperimentService, File, GTest, JSONDict, Resource,
                      Settings, Shell, StrParam, Table, TableFilter,
                      TableImporter, TaskInputs, TaskModel, TaskOutputs,
                      TaskRunner, task_decorator)

settings = Settings.retrieve()
testdata_dir = settings.get_variable("gws_core:testdata_dir")


class TestTableFilter(BaseTestCase):

    async def test_multi_index_table(self):
        GTest.print("Multi Index Table")

        file = File(path=os.path.join(testdata_dir, "multi_index_data.csv"))
        tester = TaskRunner(
            params={"header": 0, "index_columns": ["Name"]},
            inputs={"file": file},
            task_type=TableImporter,
        )
        outputs = await tester.run()
        table = outputs["resource"]
        print(table)

        # filter columns
        tester = TaskRunner(
            params={
                "axis_name_filter": [{"axis_type": "column", "value": "Ag.*"}]
            },
            inputs={"table": table},
            task_type=TableFilter,
        )
        outputs = await tester.run()
        filtered_table = outputs["table"]
        self.assertEqual(filtered_table.column_names, ["Age"])
        self.assertEqual(filtered_table.row_names, ["Luc", "Lea", "Laura", "Leon"])
        print(filtered_table)

        # filter columns and rows
        tester = TaskRunner(
            params={
                "axis_name_filter": [
                    {"axis_type": "column", "value": "Ag.*"},
                    {"axis_type": "row", "value": "Luc|Lea"}
                ]
            },
            inputs={"table": table},
            task_type=TableFilter,
        )
        outputs = await tester.run()
        filtered_table = outputs["table"]
        self.assertEqual(filtered_table.column_names, ["Age"])
        self.assertEqual(filtered_table.row_names, ["Luc", "Lea"])

        # filter aggregation
        tester = TaskRunner(
            params={
                "aggregation_filter": [
                    {"direction": "horizontal", "function": "var", "comparator": ">=", "value": 50},
                ]
            },
            inputs={"table": table},
            task_type=TableFilter,
        )
        outputs = await tester.run()
        filtered_table = outputs["table"]
        self.assertEqual(filtered_table.row_names, ["Laura", "Leon"])
        self.assertEqual(filtered_table.column_names, ["Age", "Sex", "City", "Weight"])

        # filter numeric data
        tester = TaskRunner(
            params={
                "numeric_data_filter": [
                    {"column_name": "Age|Weight", "comparator": ">=", "value": 30},
                ]
            },
            inputs={"table": table},
            task_type=TableFilter,
        )
        outputs = await tester.run()
        filtered_table = outputs["table"]
        self.assertEqual(filtered_table.row_names, ["Laura", "Leon"])
        self.assertEqual(filtered_table.column_names, ["Age", "Sex", "City", "Weight"])

        # filter str data
        tester = TaskRunner(
            params={
                "text_data_filter": [
                    {"column_name": "Sex", "comparator": "!=", "value": "M"},
                ]
            },
            inputs={"table": table},
            task_type=TableFilter,
        )
        outputs = await tester.run()
        filtered_table = outputs["table"]
        self.assertEqual(filtered_table.row_names, ["Lea", "Laura"])
        self.assertEqual(filtered_table.column_names, ["Age", "Sex", "City", "Weight"])

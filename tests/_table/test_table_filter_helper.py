# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from gws_core import (BaseTestCase, BoolParam, ConfigParams, Experiment,
                      ExperimentService, File, GTest, JSONDict, Resource,
                      Settings, Shell, StrParam, Table, TableFilterHelper,
                      TableImporter, TaskInputs, TaskModel, TaskOutputs,
                      TaskTester, task_decorator)

settings = Settings.retrieve()
testdata_dir = settings.get_variable("gws_core:testdata_dir")


class TestTableFilterHelper(BaseTestCase):
    async def test_table_filter_helper(self):
        file = File(path=os.path.join(testdata_dir, "multi_index_data.csv"))
        tester = TaskTester(
            params={"header": 0, "index_columns": ["Name"]},
            inputs={"file": file},
            task_type=TableImporter,
        )
        outputs = await tester.run()
        table = outputs["resource"]
        print(table)

        # filter by row name
        df = TableFilterHelper.filter_by_axis_names(
            data=table.get_data(), axis="row", pattern="L.*a$"
        )
        self.assertEqual(df.index.tolist(), ["Lea", "Laura"])
        self.assertEqual(df.columns.tolist(), ["Age", "Sex", "City", "Weight"])

        # filter by column name
        df = TableFilterHelper.filter_by_axis_names(
            data=table.get_data(), axis="column", pattern="Cit*"
        )
        self.assertEqual(df.index.tolist(), ["Luc", "Lea", "Laura", "Leon"])
        self.assertEqual(df.columns.tolist(), ["City"])

        # filter by aggreated column
        df = TableFilterHelper.filter_by_aggregated_values(
            data=table.get_data(), direction="vertical", func="sum", comp=">=", value=100
        )
        self.assertEqual(df.index.tolist(), ["Luc", "Lea", "Laura", "Leon"])
        self.assertEqual(df.columns.tolist(), ["Age", "Weight"])

        # filter by aggreated column
        df = TableFilterHelper.filter_by_aggregated_values(
            data=table.get_data(), direction="vertical", func="sum", comp=">=", value=150
        )
        self.assertEqual(df.index.tolist(), ["Luc", "Lea", "Laura", "Leon"])
        self.assertEqual(df.columns.tolist(), ["Weight"])

        # filter by aggreated column
        df = TableFilterHelper.filter_by_aggregated_values(
            data=table.get_data(), direction="vertical", func="sum", comp="<", value=150
        )
        self.assertEqual(df.index.tolist(), ["Luc", "Lea", "Laura", "Leon"])
        self.assertEqual(df.columns.tolist(), ["Age"])

        # filter by aggreated column
        df = TableFilterHelper.filter_by_aggregated_values(
            data=table.get_data(), direction="vertical", func="median", comp=">=", value=150
        )
        self.assertTrue(df.empty)

        # filter by aggreated row
        df = TableFilterHelper.filter_by_aggregated_values(
            data=table.get_data(), direction="horizontal", func="var", comp=">=", value=50
        )
        self.assertEqual(df.index.tolist(), ["Laura", "Leon"])
        self.assertEqual(df.columns.tolist(), ["Age", "Sex", "City", "Weight"])

        # filter numeric data
        df = TableFilterHelper.filter_numeric_data(
            data=table.get_data(), column_name="Age", comp=">=", value=30
        )
        self.assertEqual(df.index.tolist(), ["Laura", "Leon"])
        self.assertEqual(df.columns.tolist(), ["Age", "Sex", "City", "Weight"])

        # filter numeric data
        df = TableFilterHelper.filter_numeric_data(
            data=table.get_data(), column_name="Age|Weight", comp=">=", value=30
        )
        self.assertEqual(df.index.tolist(), ["Laura", "Leon"])
        self.assertEqual(df.columns.tolist(), ["Age", "Sex", "City", "Weight"])

        df = TableFilterHelper.filter_numeric_data(
            data=table.get_data(), column_name="Age|Sex", comp=">=", value=30
        )
        self.assertTrue(df.empty)

        df = TableFilterHelper.filter_text_data(
            data=table.get_data(), column_name="Sex", comp="==", text="M"
        )
        self.assertEqual(df.index.tolist(), ["Luc", "Leon"])
        self.assertEqual(df.columns.tolist(), ["Age", "Sex", "City", "Weight"])

        df = TableFilterHelper.filter_text_data(
            data=table.get_data(), column_name="Sex", comp="!=", text="M"
        )
        self.assertEqual(df.index.tolist(), ["Lea", "Laura"])
        self.assertEqual(df.columns.tolist(), ["Age", "Sex", "City", "Weight"])

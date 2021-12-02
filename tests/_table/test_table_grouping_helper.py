# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import math
import os

from gws_core import (AnnotatedTable, BaseTestCase, BoolParam, ConfigParams,
                      Experiment, ExperimentService, File, GTest, JSONDict,
                      Resource, Settings, Shell, StrParam, Table,
                      TableGroupingHelper, TableImporter, TaskInputs,
                      TaskModel, TaskOutputs, TaskRunner, task_decorator)
from pandas import Series

settings = Settings.retrieve()
testdata_dir = settings.get_variable("gws_core:testdata_dir")


class TestTableGroupingHelper(BaseTestCase):
    async def test_table_grouping_helper(self):
        file_path = os.path.join(testdata_dir, "annotated_table.csv")
        table = AnnotatedTable.import_from_path(File(path=file_path), params=ConfigParams({
            "index_columns": [0],
            "delimiter": ",",
        }))

        print(table)

        data = TableGroupingHelper.group_data(
            data=table.get_data(),
            key="Gender"
        )

        self.assertEqual(data.columns.to_list(), ["Gender:F", "Gender:M"])
        self.assertEqual(data.iloc[0, 0], 2.0)
        self.assertEqual(data.iloc[4, 0], 4.0)
        self.assertEqual(data.iloc[7, 0], 10.0)
        self.assertTrue(math.isnan(data.iloc[8, 0]))
        self.assertTrue(math.isnan(data.iloc[15, 0]))

        self.assertEqual(data.iloc[0, 1], 1.0)
        self.assertEqual(data.iloc[4, 1], 3.0)
        self.assertEqual(data.iloc[7, 1], 9.0)
        self.assertTrue(math.isnan(data.iloc[6, 1]))
        self.assertEqual(data.iloc[15, 1], 12.0)

        print(data)

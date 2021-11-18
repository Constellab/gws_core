# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from gws_core import (BaseTestCase, BoolParam, ConfigParams, Experiment,
                      ExperimentService, File, GTest, JSONDict, Resource,
                      Settings, Shell, StrParam, Table, TableAggregatorHelper,
                      TableImporter, TaskInputs, TaskModel, TaskOutputs,
                      TaskRunner, task_decorator)
from pandas import Series

settings = Settings.retrieve()
testdata_dir = settings.get_variable("gws_core:testdata_dir")


class TestTableAggregatorHelper(BaseTestCase):
    async def test_table_aggregator_helper(self):
        file = File(path=os.path.join(testdata_dir, "multi_index_data.csv"))
        tester = TaskRunner(
            params={"header": 0, "index_columns": ["Name"]},
            inputs={"file": file},
            task_type=TableImporter,
        )
        outputs = await tester.run()
        table = outputs["resource"]

        df = TableAggregatorHelper.aggregate(data=table.get_data(), direction="vertical", func="sum")
        exptect_df = Series(data=[110, 170], index=["Age", "Weight"])
        self.assertTrue(df.equals(exptect_df))

        df = TableAggregatorHelper.aggregate(data=table.get_data(), direction="vertical", func="mean")
        exptect_df = Series(data=[27.5, 42.5], index=["Age", "Weight"])
        self.assertTrue(df.equals(exptect_df))

        df = TableAggregatorHelper.aggregate(data=table.get_data(), direction="horizontal", func="median")
        exptect_df = Series(data=[12.5, 16.0, 59.0, 52.5], index=["Luc", "Lea", "Laura", "Leon"])
        self.assertTrue(df.equals(exptect_df))

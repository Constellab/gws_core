# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from gws_core import (BaseTestCase, BoolParam, ConfigParams, Experiment,
                      ExperimentService, File, GTest, JSONDict, Resource,
                      Settings, Shell, StrParam, Table, TableFilter,
                      TaskInputs, TaskModel, TaskOutputs, TaskTester,
                      task_decorator)

settings = Settings.retrieve()
testdata_dir = settings.get_variable("gws_core:testdata_dir")


class TestTableFilter(BaseTestCase):
    async def test_table_filter(self):
        pass
        # file_path = os.path.join(testdata_dir, "data.csv")
        # table = Table.import_from_path(File(path=file_path), params=ConfigParams())
        # tester = TaskTester(
        #     params={},
        #     inputs={"table": table},
        #     task_type=TableFilter,
        # )
        # outputs = await tester.run()

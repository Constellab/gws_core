# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import BaseTestCase, LiveTask, Table, TaskRunner
from pandas import DataFrame


class TestLiveTask(BaseTestCase):

    async def test_live_task(self):
        tester = TaskRunner(
            params={
                "code": [
                    "from pandas import DataFrame",
                    "from gws_core import Table",
                    "x = a+b",
                    "df = DataFrame({'col1': [1,x], 'col2': [0,x+1]})",
                    "output = Table(data=df)",
                ],
                "params": ["a=1", "b=2"]
            },
            task_type=LiveTask
        )

        output = await tester.run()
        table = output["target"]

        self.assertTrue(isinstance(table, Table))

        df = table.get_data()
        expected_df = DataFrame({'col1': [1, 3], 'col2': [0, 4]})
        self.assertTrue(df.equals(expected_df))

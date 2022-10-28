# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import BaseTestCase, PyLiveTask, Table, TaskRunner, Text
from pandas import DataFrame


class TestLiveTask(BaseTestCase):

    async def test_live_task(self):
        tester = TaskRunner(
            params={
                "code": [
                    "from pandas import DataFrame",
                    "from gws_core import Table",

                    "a = params['a']",
                    "b = params['b']",
                    "df = DataFrame({'col1': [1,a], 'col2': [0,b]})",

                    "source = inputs['source']",
                    "df = df + source.get_data()",

                    "# the target resource will be given to the outputs if it is defined",
                    "outputs = {'target': Table(data=df)}",
                ],
                "params": ["a=1", "b=2"],
            },
            inputs={
                'source': Table(data=DataFrame({'col1': [0, 1], 'col2': [0, 2]}))
            },
            task_type=PyLiveTask
        )

        outputs = await tester.run()
        table = outputs["target"]

        self.assertTrue(isinstance(table, Table))

        df = table.get_data()
        expected_df = DataFrame({'col1': [1, 2], 'col2': [0, 4]})
        self.assertTrue(df.equals(expected_df))

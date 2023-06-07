# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from unittest import TestCase

from pandas import DataFrame

from gws_core.impl.live.py_live_task import PyLiveTask
from gws_core.impl.openai.open_ai_chat import OpenAiChatDict
from gws_core.impl.table.table import Table
from gws_core.impl.table.transformers.table_smart_transformer import \
    TableSmartTransformer
from gws_core.impl.text.text import Text
from gws_core.task.task_runner import TaskRunner


# test_table_smart_transformer
class TestTableSmartTransformer(TestCase):

    def test_table_smart_transformer(self):
        initial_df = DataFrame({'A': [1, 2, 3, 4], 'B': [8, 6, 4, 9]})
        table: Table = Table(initial_df, column_tags=[{"name": "A"}, {"name": "B"}])

        # Simulate a chat with openAI
        prompt: OpenAiChatDict = {
            "messages":  [{
                "role": "user",
                "content": "Remove column where average value is lower than 5",
            }, {
                "role": "assistant",
                "content": "Here is the result : ```target = source.loc[:, source.mean() >= 5]```"
            }]
        }
        tester = TaskRunner(
            task_type=TableSmartTransformer,
            inputs={
                "source": table,
            },
            params={
                'prompt': prompt,
                "keep_columns_tags": True,
            }
        )

        outputs = tester.run()

        # check the result table and tags
        target: Table = outputs["target"]
        expected_df = DataFrame({'B': [8, 6, 4, 9]})
        expected_table: Table = Table(expected_df, column_tags=[{"name": "B"}])
        self.assertTrue(target.equals(expected_table))

        # check the generated code
        # Try to execute the code in a python live task
        code: Text = outputs["generated_code"]

        tester = TaskRunner(
            task_type=PyLiveTask,
            inputs={
                'source': table,
            },
            params={
                'code': code.get_data(),
            }
        )

        outputs = tester.run()

        # check the result table and tags
        target_2: Table = outputs["target"]
        self.assertTrue(target_2.equals(expected_table))



from unittest import TestCase

from pandas import DataFrame

from gws_core.impl.live.py_agent import PyAgent
from gws_core.impl.openai.open_ai_types import OpenAiChatDict
from gws_core.impl.table.table import Table
from gws_core.impl.table.transformers.table_smart_transformer import \
    TableSmartTransformer
from gws_core.impl.text.text import Text
from gws_core.task.task_runner import TaskRunner


# test_table_smart_transformer
class TestTableSmartTransformer(TestCase):

    def test_table_smart_transformer(self):
        initial_df = DataFrame({'A': [1, 2, 3, 4], 'B': [8, 6, 4, 9]})
        table: Table = Table(initial_df, column_tags=[
                             {"name": "A"}, {"name": "B"}])

        # Simulate a real chat with openAI, this expects a response from the assistant
        prompt: OpenAiChatDict = {
            "messages":  [{
                "role": "user",
                "content": "Remove column where average value is lower than 5",
            },
                #     {
                #     "role": "assistant",
                #     "content": "Here is the result : ```target = source.loc[:, source.mean() >= 5]```"
                # }
            ]
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
        # Try to execute the code in a python agent
        code: Text = outputs["generated_code"]

        tester = TaskRunner(
            task_type=PyAgent,
            inputs={
                'source': table,
            },
            params={
                'code': code.get_data(),
                'params': {}
            }
        )

        outputs = tester.run()

        # check the result table and tags
        target_2: Table = outputs["target"]
        self.assertTrue(target_2.equals(expected_table))

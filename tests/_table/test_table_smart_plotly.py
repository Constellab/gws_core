# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from unittest import TestCase

from pandas import DataFrame

from gws_core.impl.json.json_dict import JSONDict
from gws_core.impl.live.py_live_task import PyLiveTask
from gws_core.impl.openai.open_ai_chat import OpenAiChatDict
from gws_core.impl.table.table import Table
from gws_core.impl.table.transformers.table_smart_plotly import SmartPlotly
from gws_core.impl.text.text import Text
from gws_core.resource.view.view import View
from gws_core.task.task_runner import TaskRunner


# test_table_smart_plotly
class TestSmartPlotly(TestCase):

    def test_smart_plotly(self):
        initial_df = DataFrame({'A': [1, 2, 3, 4], 'B': [8, 6, 4, 9]})
        table: Table = Table(initial_df)

        # Simulate a chat with openAI
        prompt: OpenAiChatDict = {
            "messages":  [{
                "role": "user",
                "content": "Generate a scatter plot",
            }, {
                "role": "assistant",
                "content": """Here is the result : ```import plotly.express as px

target = px.scatter(source, x="A", y="B")```"""
            }]
        }
        tester = TaskRunner(
            task_type=SmartPlotly,
            inputs={
                "source": table,
            },
            params={
                'prompt': prompt,
            }
        )

        outputs = tester.run()

        # check the result table and tags
        target: JSONDict = outputs["target"]
        self.assertTrue(View.json_is_from_view(target.get_data()))

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

        # check the result are the same
        target_2: JSONDict = outputs["target"]
        self.assertTrue(target.equals(target_2))

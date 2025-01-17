

from unittest import TestCase

from gws_core.impl.agent.py_agent import PyAgent
from gws_core.impl.file.file import File
from gws_core.impl.openai.open_ai_types import OpenAiChatDict
from gws_core.impl.table.table import Table
from gws_core.impl.table.transformers.table_smart_plot import SmartPlot
from gws_core.impl.text.text import Text
from gws_core.task.task_runner import TaskRunner
from pandas import DataFrame


# test_table_smart_plot
class TestSmartPlot(TestCase):

    def test_table_smart_transformer(self):
        initial_df = DataFrame({'A': [1, 2, 3, 4], 'B': [8, 6, 4, 9]})
        table: Table = Table(initial_df)

        # Simulate a chat with openAI
        prompt: OpenAiChatDict = {
            "messages":  [{
                "role": "user",
                "content": "Generate a box plot, one bar per column",
            }, {
                "role": "assistant",
                "content": """Here is the result : ```import matplotlib.pyplot as plt

fig, axs = plt.subplots(ncols=7, figsize=(20,5))

for i, col in enumerate(source.columns):
    if source[col].dtype != 'object':
        axs[i].boxplot(source[col])
        axs[i].set_title(col)

plt.savefig(output_path)```"""
            }]
        }
        tester = TaskRunner(
            task_type=SmartPlot,
            inputs={
                "source": table,
            },
            params={
                'prompt': prompt,
            }
        )

        outputs = tester.run()

        # check the result table and tags
        target: File = outputs["target"]
        self.assertTrue(target.is_image())
        self.assertTrue(target.exists())

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
        target_2: File = outputs["target"]
        self.assertTrue(target_2.is_image())
        self.assertTrue(target_2.exists())

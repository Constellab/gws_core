# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from unittest import TestCase

from gws_core.impl.json.json_dict import JSONDict
from gws_core.impl.json.json_smart_transformer import JsonSmartTransformer
from gws_core.impl.live.py_live_task import PyLiveTask
from gws_core.impl.openai.open_ai_types import OpenAiChatDict
from gws_core.impl.text.text import Text
from gws_core.task.task_runner import TaskRunner


# test_json_smart_transformer
class TestJsonSmartTransformer(TestCase):

    def test_smart_plotly(self):
        json_dict: JSONDict = JSONDict({
            "name": "test",
            "scores": [1, 2, 3, 4],
        })

        # Simulate a chat with openAI, to remove scores lower than 3
        prompt: OpenAiChatDict = {
            "messages":  [{
                "role": "user",
                "content": "Generate a scatter plot",
            }, {
                "role": "assistant",
                "content": """Here is the result : ```# Create a new list that only contains scores higher than or equal to 3
filtered_scores = [score for score in source['scores'] if score >= 3]

# Create a new 'target' json object and assign the modified 'source' object to it
target = source.copy()
target['scores'] = filtered_scores```"""
            }]
        }
        tester = TaskRunner(
            task_type=JsonSmartTransformer,
            inputs={
                "source": json_dict,
            },
            params={
                'prompt': prompt,
            }
        )

        outputs = tester.run()

        # check the result table and tags
        target: JSONDict = outputs["target"]
        self.assertIsInstance(target, JSONDict)

        expected_json = JSONDict({
            "name": "test",
            "scores": [3, 4],
        })
        self.assertTrue(target.equals(expected_json))

        # check the generated code
        # Try to execute the code in a python live task
        code: Text = outputs["generated_code"]

        tester = TaskRunner(
            task_type=PyLiveTask,
            inputs={
                'source': json_dict,
            },
            params={
                'code': code.get_data(),
            }
        )
        outputs = tester.run()

        # check the result are the same
        target_2: JSONDict = outputs["target"]
        self.assertTrue(target.equals(target_2))

from unittest import TestCase

from pandas import DataFrame

from gws_core.impl.openai.open_ai_types import OpenAiChatDict
from gws_core.impl.table.smart_tasks.table_smart_multi_transformer import MultiTableSmartTransformer
from gws_core.impl.table.table import Table
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.resource.resource_set.resource_list import ResourceList
from gws_core.task.task_runner import TaskRunner


# test_multi_table_smart_transformer
class TestMultiTableSmartTransformer(TestCase):
    def test_multi_table_smart_transformer(self):
        first_table = Table(DataFrame({"A": [1, 2, 3, 4]}))
        second_table = Table(DataFrame({"B": [8, 6, 4, 9]}))

        resource_list = ResourceList([first_table, second_table])

        # Simulate a real chat with openAI, this expects a response from the assistant
        prompt: OpenAiChatDict = {
            "messages": [
                {
                    "role": "user",
                    "content": "Remove column where average value is lower than 5",
                },
                {
                    "role": "assistant",
                    "content": """Here is the result :
```
target = []

# Looping through each dataframe in the source list
for df in source:
    # Transposing the dataframe using the T attribute
    transposed_df = df.T

    # Appending the transposed dataframe to the target list
    target.append(transposed_df)```""",
                },
            ]
        }
        tester = TaskRunner(
            task_type=MultiTableSmartTransformer,
            inputs={
                "source": resource_list,
            },
            params={
                "prompt": prompt,
            },
            # need to override this to make dynamic io work
            input_specs=InputSpecs(
                {
                    "source": InputSpec(ResourceList),
                }
            ),
            output_specs=OutputSpecs(
                {
                    "target": OutputSpec(ResourceList),
                }
            ),
        )

        outputs = tester.run()

        # check the result table and tags
        target: ResourceList = outputs["target"]
        self.assertEqual(len(target), 2)

        # check the first table
        self.assertTrue(first_table.transpose().equals(target[0]))

        # check the second table
        self.assertTrue(second_table.transpose().equals(target[1]))

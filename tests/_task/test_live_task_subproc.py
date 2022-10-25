# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import BaseTestCase, LiveTask, Table, TaskRunner, Text
from pandas import DataFrame


class TestLiveTask(BaseTestCase):

    async def test_live_task_shell(self):
        tester = TaskRunner(
            params={
                "code": [
                    "from gws_core import Text",
                    "import subprocess",
                    "import sys",
                    "result = subprocess.run([sys.executable, '-c', 'print(\"gencovery\")'], capture_output=True, text=True)",
                    "target = Text(data=result.stdout)",
                ],
                "params": []
            },
            task_type=LiveTask
        )

        outputs = await tester.run()
        text = outputs["target"]
        self.assertTrue(isinstance(text, Text))
        self.assertEqual(text.get_data().strip(), 'gencovery')

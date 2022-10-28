# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import BaseTestCase, PyLiveTask, Table, TaskRunner, Text
from pandas import DataFrame


class TestLiveTaskShellProxy(BaseTestCase):

    async def test_live_task_shell(self):
        tester = TaskRunner(
            params={
                "code": [
                    "import os",
                    "from gws_core import Text, ShellProxy",
                    "shell_proxy = ShellProxy()",
                    "shell_proxy.run([f'echo \"constellab\" > echo.txt'], shell_mode=True)",
                    "result_file_path = os.path.join(shell_proxy.working_dir, 'echo.txt')",
                    "with open(result_file_path, 'r+t') as fp:",
                    "    data = fp.read()",
                    "shell_proxy.clean_working_dir()",
                    "target = Text(data=data)",
                ],
                "params": []
            },
            task_type=PyLiveTask
        )

        outputs = await tester.run()
        text = outputs["target"]
        self.assertTrue(isinstance(text, Text))
        self.assertEqual(text.get_data().strip(), 'constellab')

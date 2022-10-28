# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import BaseTestCase, PyLiveTask, Table, TaskRunner, Text
from pandas import DataFrame


class TestLiveTaskPipenv(BaseTestCase):

    async def test_live_task_shell(self):
        tester = TaskRunner(
            params={
                "code": ["""
import os
from gws_core import Text

yml_text = " \\
name: .venv3\\n \\
channels:\\n \\
- conda-forge\\n \\
dependencies:\\n \\
- python=3.8\\n \\
- pyjwt"
shell_proxy = self.create_conda_shell_proxy(yml_text)

cmd = ["python", os.path.join(__cdir__, "penv", "jwt_encode.py"), ">", "out.txt"]
shell_proxy.run(cmd, shell_mode=True)
result_file_path = os.path.join(shell_proxy.working_dir, 'out.txt')

with open(result_file_path, 'r+t') as fp:
    data = fp.read()
shell_proxy.clean_working_dir()
target = Text(data=data)
"""
                         ],
            },
            task_type=PyLiveTask
        )

        outputs = await tester.run()
        text = outputs["target"]
        self.assertTrue(isinstance(text, Text))
        self.assertEqual(text.get_data().strip(), 'constellab')

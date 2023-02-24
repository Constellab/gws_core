# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from pandas import DataFrame

from gws_core import BaseTestCase, PyLiveTask, Table, TaskRunner, Text


# test_py_live_task
class TestLiveTask(BaseTestCase):

    def test_live_task(self):
        tester = TaskRunner(
            params={
                "code": """
from pandas import DataFrame
from gws_core import Table

def foo(a,b,source):
    df = Table(DataFrame({'col1': [1,a], 'col2': [0,b]}))
    df = df.get_data() + source.get_data()

    # the target resource will be given to the outputs if it is defined
    outputs = {'target': Table(data=df)}
    return outputs

a = params['a']
b = params['b']
source = inputs['source']
outputs = foo(a,b,source)
            """,
                "params": ["a=1", "b=2"],
            },
            inputs={
                'source': Table(data=DataFrame({'col1': [0, 1], 'col2': [0, 2]}))
            },
            task_type=PyLiveTask
        )

        outputs = tester.run()
        table: Table = outputs["target"]

        self.assertTrue(isinstance(table, Table))

        expected_table = Table(DataFrame({'col1': [1, 2], 'col2': [0, 4]}))
        self.assertTrue(table.equals(expected_table))

    def test_live_task_shell_with_subproc(self):
        tester = TaskRunner(
            params={
                "code": """
from gws_core import Text
import subprocess
import sys
result = subprocess.run([sys.executable, '-c', 'print(\"gencovery\")'], capture_output=True, text=True)
target = Text(data=result.stdout)
outputs = {"target": target}
                """,
                "params": []
            },
            task_type=PyLiveTask
        )

        outputs = tester.run()
        text = outputs["target"]
        self.assertTrue(isinstance(text, Text))

    def test_live_task_shell_with_shellproxy(self):
        tester = TaskRunner(
            params={
                "code": """
import os
from gws_core import Text, ShellProxy
shell_proxy = ShellProxy()
shell_proxy.run([f'echo \"constellab\" > echo.txt'], shell_mode=True)
result_file_path = os.path.join(shell_proxy.working_dir, 'echo.txt')
with open(result_file_path, 'r+t') as fp:
    data = fp.read()
shell_proxy.clean_working_dir()
target = Text(data=data)
outputs = {"target": target}
                """,
                "params": []
            },
            task_type=PyLiveTask
        )

        outputs = tester.run()
        text = outputs["target"]
        self.assertTrue(isinstance(text, Text))
        self.assertEqual(text.get_data().strip(), 'constellab')

#     def test_live_task_shell_with_pipenv(self):
#         tester = TaskRunner(
#             params={
#                 "code": """
# import os
# from gws_core import Text, EnvShellProxyHelper

# yml_text = " \\
# name: .venv3\\n \\
# channels:\\n \\
# - conda-forge\\n \\
# dependencies:\\n \\
# - python=3.8\\n \\
# - pyjwt"
# shell_proxy = EnvShellProxyHelper.create_conda_shell_proxy(yml_text)

# cmd = ["python", os.path.join(__cdir__, "penv", "jwt_encode.py"), ">", "out.txt"]
# shell_proxy.run(cmd, shell_mode=True)
# result_file_path = os.path.join(shell_proxy.working_dir, 'out.txt')

# with open(result_file_path, 'r+t') as fp:
#     data = fp.read()
# shell_proxy.clean_working_dir()
# target = Text(data=data)
# outputs = {"target": target}
# """,
#             },
#             task_type=PyLiveTask
#         )

#         outputs = tester.run()
#         text = outputs["target"]
#         self.assertTrue(isinstance(text, Text))
#         self.assertEqual(text.get_data().strip(), 'constellab')

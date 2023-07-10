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


df = Table(DataFrame({'col1': [1,a], 'col2': [0,b]}))
df = df.get_data() + source[0].get_data()

# return Dataframe (it should be converted to table)
target = [df]

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
target = [Text(data=result.stdout)]
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
target = [Text(data=data)]
                """,
                "params": []
            },
            task_type=PyLiveTask
        )

        outputs = tester.run()
        text: Text = outputs["target"]
        self.assertTrue(isinstance(text, Text))
        self.assertEqual(text.get_data().strip(), 'constellab')

    def test_live_task_with_exception(self):
        tester = TaskRunner(
            params={
                "code": """
raise Exception('This is not working')
""",
                "params": []
            },
            task_type=PyLiveTask
        )

        error = False
        try:
            tester.run()
        except Exception as err:
            error = True
            # check that the error of the snippet is the same as the one raised
            self.assertEqual(str(err), 'This is not working')

        self.assertTrue(error)

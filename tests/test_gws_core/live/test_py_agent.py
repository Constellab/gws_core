

from pandas import DataFrame

from gws_core import BaseTestCase, PyAgent, Table, TaskRunner, Text


# test_py_agent
class TestAgent(BaseTestCase):

    def test_default_config(self):
        """Test the default py agent config template to be sure it is valid
        """
        data = DataFrame({'col1': [0, 1], 'col2': [0, 2]})
        tester = TaskRunner(
            inputs={'source': Table(data)},
            task_type=PyAgent
        )

        outputs = tester.run()
        table: Table = outputs["target"]

        self.assertTrue(isinstance(table, Table))

        expected_table = Table(data.T)
        self.assertTrue(table.equals(expected_table))

    def test_agent(self):
        tester = TaskRunner(
            params={
                "code": """
from pandas import DataFrame
from gws_core import Table


df = Table(DataFrame({'col1': [1,a], 'col2': [0,b]}))
df = df.get_data() + sources[0].get_data()

# return Dataframe (it should be converted to table)
targets = [df]

            """,
                "params": ["a=1", "b=2"],
            },
            inputs={
                'source': Table(data=DataFrame({'col1': [0, 1], 'col2': [0, 2]}))
            },
            task_type=PyAgent
        )

        outputs = tester.run()
        table: Table = outputs["target"]

        self.assertTrue(isinstance(table, Table))

        expected_table = Table(DataFrame({'col1': [1, 2], 'col2': [0, 4]}))
        self.assertTrue(table.equals(expected_table))

    def test_agent_shell_with_subproc(self):
        tester = TaskRunner(
            params={
                "code": """
from gws_core import Text
import subprocess
import sys
result = subprocess.run([sys.executable, '-c', 'print(\"gencovery\")'], capture_output=True, text=True)
targets = [Text(data=result.stdout)]
                """,
                "params": []
            },
            task_type=PyAgent
        )

        outputs = tester.run()
        text = outputs["target"]
        self.assertTrue(isinstance(text, Text))

    def test_agent_shell_with_shellproxy(self):
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
targets = [Text(data=data)]
                """,
                "params": []
            },
            task_type=PyAgent
        )

        outputs = tester.run()
        text: Text = outputs["target"]
        self.assertTrue(isinstance(text, Text))
        self.assertEqual(text.get_data().strip(), 'constellab')

    def test_agent_with_exception(self):
        tester = TaskRunner(
            params={
                "code": """
raise Exception('This is not working')
""",
                "params": []
            },
            task_type=PyAgent
        )

        error = False
        try:
            tester.run()
        except Exception as err:
            error = True
            # check that the error of the snippet is the same as the one raised
            self.assertEqual(str(err), 'This is not working')

        self.assertTrue(error)

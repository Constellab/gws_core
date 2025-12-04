from pandas import DataFrame

from gws_core import BaseTestCase, PyAgent, Table, TaskRunner
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.code_param.python_code_param import PythonCodeParam
from gws_core.config.param.dynamic_param import DynamicParam
from gws_core.config.param.param_spec import IntParam


# test_py_agent
class TestAgent(BaseTestCase):
    def test_default_config(self):
        """Test the default py agent config template to be sure it is valid"""
        data = DataFrame({"col1": [0, 1], "col2": [0, 2]})
        tester = TaskRunner(
            inputs={"source": Table(data)}, params={"params": {}}, task_type=PyAgent
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


df = Table(DataFrame({'col1': [1,params['a']], 'col2': [0,params['b']]}))
df = df.get_data() + sources[0].get_data()

# return Dataframe (it should be converted to table)
targets = [df]

            """,
                "params": {"a": 1, "b": 2},
            },
            inputs={"source": Table(data=DataFrame({"col1": [0, 1], "col2": [0, 2]}))},
            config_specs=ConfigSpecs(
                {
                    "params": DynamicParam(specs=ConfigSpecs({"a": IntParam(), "b": IntParam()})),
                    "code": PythonCodeParam(),
                }
            ),
            task_type=PyAgent,
        )

        outputs = tester.run()
        table: Table = outputs["target"]

        self.assertTrue(isinstance(table, Table))

        expected_table = Table(DataFrame({"col1": [1, 2], "col2": [0, 4]}))
        self.assertTrue(table.equals(expected_table))

    def test_agent_with_exception(self):
        tester = TaskRunner(
            params={
                "code": """
raise Exception('This is not working')
""",
                "params": {},
            },
            task_type=PyAgent,
        )

        error = False
        try:
            tester.run()
        except Exception as err:
            error = True
            # check that the error of the snippet is the same as the one raised
            self.assertEqual(str(err), "This is not working")

        self.assertTrue(error)

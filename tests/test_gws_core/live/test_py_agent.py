

from typing import Any, Dict

from pandas import DataFrame

from gws_core import BaseTestCase, PyAgent, Table, TaskRunner, Text
from gws_core.config.config import Config
from gws_core.config.param.dynamic_param import DynamicParam
from gws_core.config.param.param_spec import IntParam, ListParam, ParamSpec
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.protocol.protocol_service import ProtocolService


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


df = Table(DataFrame({'col1': [1,params['a']], 'col2': [0,params['b']]}))
df = df.get_data() + sources[0].get_data()

# return Dataframe (it should be converted to table)
targets = [df]

            """,
                "params": {
                    'a': 1,
                    'b': 2
                },
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
                "params": {}
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
                "params": {}
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
                "params": {}
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

    def test_add_param(self):

        proto: ProtocolModel = ProtocolService.create_empty_protocol()

        process_model = ProtocolService.add_process_to_protocol_id(
            proto.id,
            PyAgent.get_typing_name()
        ).process

        proto = proto.refresh()

        ProtocolService.add_dynamic_param_spec_of_process(
            proto.id, process_model.instance_name, 'a', IntParam(default_value=2).to_dto()
        )

        test_process_model = proto.get_process(process_model.instance_name)
        self.assertIsNotNone(test_process_model)
        self.assertIsNotNone(test_process_model.config.data.get('specs').get(
            'params').get('additional_info').get('specs').get('a'))
        self.assertIsNotNone(test_process_model.config.get_value('params'))
        self.assertEqual(test_process_model.config.get_spec('params')
                         .specs['a'].to_dto().to_json_dict(), IntParam(default_value=2).to_dto().to_json_dict())
        self.assertEqual(test_process_model.config.get_value('params')['a'], 2)

    def test_update_param(self):

        proto: ProtocolModel = ProtocolService.create_empty_protocol()

        process_model = ProtocolService.add_process_to_protocol_id(
            proto.id,
            PyAgent.get_typing_name()
        ).process

        proto = proto.refresh()

        ProtocolService.add_dynamic_param_spec_of_process(
            proto.id, process_model.instance_name, 'a', IntParam(default_value=2).to_dto()
        )

        ProtocolService.update_dynamic_param_spec_of_process(
            proto.id, process_model.instance_name, 'a', IntParam(default_value=3).to_dto()
        )

        test_process_model = proto.get_process(process_model.instance_name)
        self.assertIsNotNone(test_process_model)
        self.assertIsNotNone(test_process_model.config.data.get('specs').get(
            'params').get('additional_info').get('specs').get('a'))
        self.assertIsNotNone(test_process_model.config.get_value('params'))
        self.assertEqual(test_process_model.config.get_spec('params')
                         .specs['a'].to_dto().to_json_dict(), IntParam(default_value=3).to_dto().to_json_dict())
        self.assertEqual(test_process_model.config.get_value('params')['a'], 3)

    def test_remove_param(self):

        proto: ProtocolModel = ProtocolService.create_empty_protocol()

        process_model = ProtocolService.add_process_to_protocol_id(
            proto.id,
            PyAgent.get_typing_name()
        ).process

        proto = proto.refresh()

        ProtocolService.add_dynamic_param_spec_of_process(
            proto.id, process_model.instance_name, 'a', IntParam(default_value=2).to_dto()
        )

        ProtocolService.remove_dynamic_param_spec_of_process(
            proto.id, process_model.instance_name, 'a'
        )

        test_process_model = proto.get_process(process_model.instance_name)
        self.assertIsNotNone(test_process_model)
        self.assertIsNone(test_process_model.config.data.get('specs').get(
            'params').get('additional_info').get('specs').get('a'))
        self.assertIsNone(test_process_model.config.get_value('params').get('a'))

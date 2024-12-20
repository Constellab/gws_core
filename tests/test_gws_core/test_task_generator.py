

from gws_core.code.agent_factory import AgentFactory
from gws_core.config.param.code_param.python_code_param import PythonCodeParam
from gws_core.config.param.dynamic_param import DynamicParam
from gws_core.config.param.param_spec import BoolParam, IntParam, StrParam
from gws_core.core.utils.string_helper import StringHelper
from gws_core.impl.live.py_agent import PyAgent
from gws_core.process.process_factory import ProcessFactory
from gws_core.test.base_test_case import BaseTestCase


# test_task_generator
class TestTaskGenerator(BaseTestCase):

    def test_task_generator(self):

        code = """
from gws_core import Table
import json

# access task method to log a messages
self.log_info_message('Transposing table')
# Transpose the input table
table: Table = sources[0].transpose()

# set the new table a output or the agent
targets = [table]
"""

        task_model = ProcessFactory.create_task_model_from_type(
            PyAgent,
            config_params={PyAgent.CONFIG_CODE_NAME: code, PyAgent.
                           CONFIG_PARAMS_NAME: {'a': 1, 'b': '2', 'c': 3, 'd': True}, },
            instance_name='test_task_generator',
            config_specs={PyAgent.CONFIG_CODE_NAME: PythonCodeParam(),
                          PyAgent.CONFIG_PARAMS_NAME:
                          DynamicParam(
                              specs={'a': IntParam(default_value=1),
                                     'b': StrParam(default_value='2'),
                                     'c': IntParam(default_value=3),
                                     'd': BoolParam(default_value=True)})})

        result = AgentFactory.generate_task_code_from_agent(task_model)

        # print(result)

        expected_result = """
from gws_core import (BoolParam, ConfigParams, ConfigSpecs, InputSpec, InputSpecs, IntParam, OutputSpec, OutputSpecs, Resource, StrParam, Task, TaskInputs, TaskOutputs, task_decorator)
from gws_core import Table
import json


@task_decorator(unique_name="TestTaskGenerator")
class TestTaskGenerator(Task):

        input_specs: InputSpecs = InputSpecs({'resource_1': InputSpec(Resource)})
        output_specs: OutputSpecs = OutputSpecs({'resource_1': OutputSpec(Resource)})
        config_specs: ConfigSpecs = {'a': IntParam(default_value=1), 'b': StrParam(default_value='2'), 'c': IntParam(default_value=3), 'd': BoolParam(default_value=True)}

        def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

                # access task method to log a messages
                self.log_info_message('Transposing table')
                # Transpose the input table
                table: Table = sources[0].transpose()

                # set the new table a output or the agent
                targets = [table]"""

        self.assertEqual(StringHelper.remove_whitespaces(result), StringHelper.remove_whitespaces(expected_result))

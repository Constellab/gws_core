# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.code.task_generator_service import TaskGeneratorService
from gws_core.core.utils.string_helper import StringHelper
from gws_core.impl.live.py_live_task import PyLiveTask
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

# set the new table a output or the live task
targets = [table]
"""

        task_model = ProcessFactory.create_task_model_from_type(PyLiveTask, config_params={
            PyLiveTask.CONFIG_CODE_NAME: code,
            PyLiveTask.CONFIG_PARAMS_NAME: ["a = 1", "b = '2'", "c = 3", "d = True"],
        }, instance_name='test_task_generator')

        result = TaskGeneratorService.generate_task_code_from_live_task(task_model)

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

                # set the new table a output or the live task
                targets = [table]"""

        self.assertEqual(StringHelper.remove_whitespaces(result), StringHelper.remove_whitespaces(expected_result))

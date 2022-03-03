# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from gws_core import (BaseTestCase, BoolParam, ConfigParams, Experiment,
                      ExperimentService, File, GTest, Resource, Shell,
                      StrParam, TaskInputs, TaskModel, TaskOutputs,
                      TaskService, TaskRunner, task_decorator)


@task_decorator("Echo")
class Echo(Shell):
    input_specs = {}
    output_specs = {'file': File}
    config_specs = {
        'name': StrParam(optional=True, short_description="The name to echo"),
    }
    _shell_mode = True

    def build_command(self, params: ConfigParams, __: TaskInputs) -> list:
        name = params.get_value("name")
        return [f"echo \"{name}\" > echo.txt"]

    def gather_outputs(self, _: ConfigParams, __: TaskInputs) -> TaskOutputs:
        path = os.path.join(self.working_dir, "echo.txt")
        file = File(path=path)
        return {"file": file}


class TestShell(BaseTestCase):

    async def test_shell(self):
        tester = TaskRunner(
            inputs={},
            params={"name": "John Doe"},
            task_type=Echo
        )
        outputs = await tester.run()
        file = outputs["file"]
        self.assertEqual(file.read().strip(), "John Doe")

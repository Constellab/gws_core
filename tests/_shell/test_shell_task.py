# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from typing import List

from gws_core import (BaseTestCase, ConfigParams, File, OutputSpec, ShellTask,
                      StrParam, TaskInputs, TaskOutputs, TaskRunner,
                      task_decorator)
from gws_core.impl.shell.shell_proxy import ShellProxy


# test_shell_task
@task_decorator("EchoInFileTask")
class EchoInFileTask(ShellTask):
    input_specs = {}
    output_specs = {'file': OutputSpec(File)}
    config_specs = {
        'name': StrParam(optional=True, short_description="The name to echo"),
    }

    async def run_with_proxy(self, params: ConfigParams, inputs: TaskInputs,
                             shell_proxy: ShellProxy) -> TaskOutputs:
        name = params.get_value("name")
        shell_proxy.run([f"echo \"{name}\" > echo.txt"], shell_mode=True)

        path = os.path.join(self.working_dir, "echo.txt")
        file = File(path=path)
        return {"file": file}


class TestShell(BaseTestCase):

    async def test_echo_in_file(self):
        runner = TaskRunner(
            inputs={},
            params={"name": "John Doe"},
            task_type=EchoInFileTask
        )
        outputs = await runner.run()
        file: File = outputs["file"]
        self.assertEqual(file.read().strip(), "John Doe")

# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from typing import List

from gws_core import (BaseTestCase, ConfigParams, File, OutputSpec, Shell2,
                      StrParam, TaskInputs, TaskOutputs, TaskRunner,
                      task_decorator)
from gws_core.progress_bar.progress_bar import ProgressBar, ProgressBarMessage


@task_decorator("EchoInFile")
class EchoInFile(Shell2):
    input_specs = {}
    output_specs = {'file': OutputSpec(File)}
    config_specs = {
        'name': StrParam(optional=True, short_description="The name to echo"),
    }

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        name = params.get_value("name")
        self.shell_proxy.run([f"echo \"{name}\" > echo.txt"], shell_mode=True)

        path = os.path.join(self.working_dir, "echo.txt")
        file = File(path=path)
        return {"file": file}


@task_decorator("Echo")
class Echo(Shell2):
    input_specs = {}
    output_specs = {}
    config_specs = {
        'name': StrParam(optional=True, short_description="The name to echo"),
    }

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        name = params.get_value("name")
        self.shell_proxy.run([f"echo \"{name}\""], shell_mode=True)
        return {}


class TestShell(BaseTestCase):

    async def test_echo_n_file(self):
        runner = TaskRunner(
            inputs={},
            params={"name": "John Doe"},
            task_type=EchoInFile
        )
        outputs = await runner.run()
        file: File = outputs["file"]
        self.assertEqual(file.read().strip(), "John Doe")

    async def test_echo(self):
        runner = TaskRunner(
            inputs={},
            params={"name": "John Doe"},
            task_type=Echo
        )
        await runner.run()
        progress_bar: ProgressBar = runner._progress_bar

        # retrieve the John Doe message from the echo in the progress bar
        message: List[ProgressBarMessage] = [x for x in progress_bar.messages if x["text"] == "John Doe"]

        self.assertEqual(len(message), 1)

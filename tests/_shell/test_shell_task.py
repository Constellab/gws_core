# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from cProfile import run

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


@task_decorator("EchoTask")
class EchoTask(ShellTask):
    input_specs = {}
    output_specs = {}
    config_specs = {
        'name': StrParam(optional=True, short_description="The name to echo"),
    }

    async def run_with_proxy(self, params: ConfigParams, inputs: TaskInputs,
                             shell_proxy: ShellProxy) -> TaskOutputs:
        # no buffer so all message are directly dispatched
        self.message_dispatcher.interval_time_dispatched_buffer = 0
        name = params.get_value("name")
        shell_proxy.run([f"echo \"{name}\""], shell_mode=True)
        return {}


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

    async def test_echo(self):
        """Test the echo and check that is was logged in the progress bar
        """
        runner = TaskRunner(
            inputs={},
            params={"name": "John Doe"},
            task_type=EchoTask
        )

        await runner.run()

        # there should be a John Doe mesage in the progress bar
        self.assertEqual(len([x for x in runner._progress_bar.messages if x["text"] == "John Doe"]), 1)

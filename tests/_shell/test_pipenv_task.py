# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from unittest.async_case import IsolatedAsyncioTestCase

from gws_core import (ConfigParams, File, OutputSpec, PipEnvTask, TaskInputs,
                      TaskOutputs, TaskRunner, task_decorator)
from gws_core.impl.shell.pip_shell_proxy import PipShellProxy

__cdir__ = os.path.dirname(os.path.realpath(__file__))


# test_pipenv_task
@task_decorator("PipEnvTaskTester")
class PipEnvTaskTester(PipEnvTask):
    input_specs = {}
    output_specs = {'file': OutputSpec(File)}
    env_file_path = os.path.join(__cdir__, "penv", "env_jwt_pip.txt")

    async def run_with_proxy(self, params: ConfigParams, inputs: TaskInputs, shell_proxy: PipShellProxy) -> TaskOutputs:
        command = ["python", os.path.join(__cdir__, "penv", "jwt_encode.py"), ">", "out.txt"]
        shell_proxy.run(command, shell_mode=True)

        # retrieve the result
        file = File(path=os.path.join(self.working_dir, "out.txt"))
        return {"file": file}

# test_pipenv_task


class TestPipEnv(IsolatedAsyncioTestCase):

    async def test_pipenv(self):

        task_runner = TaskRunner(PipEnvTaskTester)

        try:
            output = await task_runner.run()

            file: File = output["file"]

            self.assertEqual(
                file.read().strip(),
                "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzb21lIjoicGF5bG9hZCJ9.4twFt5NiznN84AWoo1d7KO1T_yoc0Z6XOpOVswacPZg")

            task: PipEnvTaskTester = task_runner.get_task()

            self.assertTrue(task.shell_proxy.env_is_installed())
            task.shell_proxy.uninstall_env()
            # dispatched the message as the uninstall env notify a message
            task.dispatch_waiting_messages()
            self.assertFalse(task.shell_proxy.env_is_installed())
        except Exception as exception:
            task: PipEnvTaskTester = task_runner.get_task()
            if task:
                task.shell_proxy.uninstall_env()
                task.dispatch_waiting_messages()
            raise exception

    # async def test_pipenv_proxy(self):

    #     prox = ShellProxy(PipEnvTester)
    #     encoded_string = prox.check_output(
    #         ["python", os.path.join(__cdir__, "penv", "jwt_encode.py")]
    #     )
    #     self.assertEqual(
    #         encoded_string,
    #         "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzb21lIjoicGF5bG9hZCJ9.4twFt5NiznN84AWoo1d7KO1T_yoc0Z6XOpOVswacPZg")

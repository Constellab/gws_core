# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from gws_core import (BaseTestCase, ConfigParams, File, OutputSpec, PipEnvTask,
                      TaskInputs, TaskOutputs, TaskRunner, task_decorator)
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


class TestPipEnv(BaseTestCase):

    async def test_pipenv(self):

        task_runner = TaskRunner(PipEnvTaskTester)

        try:
            output = await task_runner.run()

            file: File = output["file"]

            self.assertEqual(
                file.read().strip(),
                "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzb21lIjoicGF5bG9hZCJ9.Joh1R2dYzkRvDkqv3sygm5YyK8Gi4ShZqbhK2gxcs2U")

            task: PipEnvTaskTester = task_runner.get_task()

            self.assertTrue(task.shell_proxy.env_is_installed())
            task.shell_proxy.uninstall_env()
            # dispatched the message as the uninstall env notify a message
            task.shell_proxy.dispatch_waiting_message()
            self.assertFalse(task.shell_proxy.env_is_installed())
        except Exception as exception:
            task: PipEnvTaskTester = task_runner.get_task()
            if task:
                task.shell_proxy.uninstall_env()
            raise exception

    # async def test_pipenv_proxy(self):

    #     prox = ShellProxy(PipEnvTester)
    #     encoded_string = prox.check_output(
    #         ["python", os.path.join(__cdir__, "penv", "jwt_encode.py")]
    #     )
    #     self.assertEqual(
    #         encoded_string,
    #         "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzb21lIjoicGF5bG9hZCJ9.Joh1R2dYzkRvDkqv3sygm5YyK8Gi4ShZqbhK2gxcs2U")

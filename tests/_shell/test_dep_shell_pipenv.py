# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from gws_core import (BaseTestCase, ConfigParams, File, OutputSpec,
                      PipEnvShell, TaskInputs, TaskOutputs, TaskRunner,
                      task_decorator)

__cdir__ = os.path.dirname(os.path.realpath(__file__))


# test_dep_shell_pipenv
@task_decorator("PipEnvTester")
class PipEnvTester(PipEnvShell):
    input_specs = {}
    output_specs = {'file': OutputSpec(File)}
    env_file_path = os.path.join(__cdir__, "penv", "env_jwt_pip.txt")

    def build_command(self, params: ConfigParams, inputs: TaskInputs) -> list:
        return ["python", os.path.join(__cdir__, "penv", "jwt_encode.py"), ">", "out.txt"]

    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        file = File(path=os.path.join(self.working_dir, "out.txt"))
        return {"file": file}


class TestPipEnv(BaseTestCase):

    async def test_pipenv(self):

        task_runner = TaskRunner(PipEnvTester)

        try:
            output = await task_runner.run()

            file: File = output["file"]

            self.assertEqual(
                file.read().strip(),
                "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzb21lIjoicGF5bG9hZCJ9.Joh1R2dYzkRvDkqv3sygm5YyK8Gi4ShZqbhK2gxcs2U")

            task: PipEnvTester = task_runner.get_task()

            self.assertTrue(task.is_installed())
            task.uninstall()
            self.assertFalse(task.is_installed())
        except Exception as exception:
            task: PipEnvTester = task_runner.get_task()
            if task:
                task.uninstall()
            raise exception

    # async def test_pipenv_proxy(self):

    #     prox = ShellProxy(PipEnvTester)
    #     encoded_string = prox.check_output(
    #         ["python", os.path.join(__cdir__, "penv", "jwt_encode.py")]
    #     )
    #     self.assertEqual(
    #         encoded_string,
    #         "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzb21lIjoicGF5bG9hZCJ9.Joh1R2dYzkRvDkqv3sygm5YyK8Gi4ShZqbhK2gxcs2U")
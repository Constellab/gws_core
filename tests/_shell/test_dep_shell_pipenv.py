# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from gws_core import (BaseTestCase, ConfigParams, File, OutputSpec,
                      OutputSpecs, PipEnvShell, TaskInputs, TaskOutputs,
                      TaskRunner, task_decorator)

__cdir__ = os.path.dirname(os.path.realpath(__file__))


# test_dep_shell_pipenv
@task_decorator("PipEnvTester")
class PipEnvTester(PipEnvShell):
    output_specs = OutputSpecs({'file': OutputSpec(File)})
    env_file_path = os.path.join(__cdir__, "penv", "env_jwt_pip.txt")

    def build_command(self, params: ConfigParams, inputs: TaskInputs) -> list:
        return ["python", os.path.join(__cdir__, "penv", "jwt_encode.py"), ">", "out.txt"]

    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        file = File(path=os.path.join(self.working_dir, "out.txt"))
        return {"file": file}


class TestPipEnv(BaseTestCase):

    def test_pipenv(self):

        task_runner = TaskRunner(PipEnvTester)

        try:
            output = task_runner.run()

            file: File = output["file"]

            value = file.read().strip()
            self.assertIsNotNone(value)
            self.assertTrue(len(value) > 0)

            task: PipEnvTester = task_runner.get_task()

            self.assertTrue(task.is_installed())
            task.uninstall()
            # dispatched the message as the uninstall env notify a message
            task_runner.force_dispatch_waiting_messages()
            self.assertFalse(task.is_installed())
        except Exception as exception:
            task: PipEnvTester = task_runner.get_task()
            if task:
                task.uninstall()
                task_runner.force_dispatch_waiting_messages()
            raise exception

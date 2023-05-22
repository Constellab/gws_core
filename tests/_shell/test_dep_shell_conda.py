# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from gws_core import (BaseTestCase, CondaEnvShell, ConfigParams, File,
                      OutputSpec, TaskInputs, TaskOutputs, task_decorator)
from gws_core.task.task_runner import TaskRunner

__cdir__ = os.path.dirname(os.path.realpath(__file__))


@task_decorator("CondaEnvTester")
class CondaEnvTester(CondaEnvShell):
    input_specs = {}
    output_specs = {'file': OutputSpec(File)}
    env_file_path = os.path.join(__cdir__, "penv", "env_jwt_conda.yml")

    def build_command(self, params: ConfigParams, inputs: TaskInputs) -> list:
        return [
            "python", os.path.join(
                __cdir__, "penv", "jwt_encode.py"), ">", "out.txt"
        ]

    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        file = File(path=os.path.join(self.working_dir, "out.txt"))
        return {"file": file}


class TestProcess(BaseTestCase):

    # @classmethod
    # def tearDownClass(cls):
    #     super().tearDownClass()
    #     CondaEnvTester.uninstall()

    def test_conda(self):

        task_runner = TaskRunner(CondaEnvTester)

        try:
            output = task_runner.run()

            file: File = output["file"]

            value = file.read().strip()
            self.assertIsNotNone(value)
            self.assertTrue(len(value) > 0)

            task: CondaEnvTester = task_runner.get_task()

            self.assertTrue(task.is_installed())
            task.uninstall()
            # dispatched the message as the uninstall env notify a message
            task_runner.force_dispatch_waiting_messages()
            self.assertFalse(task.is_installed())
        except Exception as exception:
            task: CondaEnvTester = task_runner.get_task()
            if task:
                task.uninstall()
                task_runner.force_dispatch_waiting_messages()
            raise exception

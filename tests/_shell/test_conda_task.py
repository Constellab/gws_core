# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from unittest import TestCase

from gws_core import (CondaEnvTask, ConfigParams, File, OutputSpec, TaskInputs,
                      TaskOutputs, task_decorator)
from gws_core.impl.shell.shell_proxy import ShellProxy
from gws_core.task.task_runner import TaskRunner

__cdir__ = os.path.dirname(os.path.realpath(__file__))


# test_conda_task
@task_decorator("CondaEnvTaskTester")
class CondaEnvTaskTester(CondaEnvTask):
    input_specs = {}
    output_specs = {'file': OutputSpec(File)}
    env_file_path = os.path.join(__cdir__, "penv", "env_jwt_conda.yml")

    def run_with_proxy(self, params: ConfigParams, inputs: TaskInputs,
                       shell_proxy: ShellProxy) -> TaskOutputs:
        command = [
            "python", os.path.join(
                __cdir__, "penv", "jwt_encode.py"), ">", "out.txt"
        ]
        shell_proxy.run(command)

        file = File(path=os.path.join(self.working_dir, "out.txt"))
        return {"file": file}


# test_conda_task
class TestCondaTask(TestCase):

    # @classmethod
    # def tearDownClass(cls):
    #     super().tearDownClass()
    #     CondaEnvTester.uninstall()

    def test_conda(self):

        task_runner = TaskRunner(CondaEnvTaskTester)

        try:
            output = task_runner.run()

            file: File = output["file"]

            value = file.read().strip()
            self.assertIsNotNone(value)
            self.assertTrue(len(value) > 0)

            task: CondaEnvTaskTester = task_runner.get_task()

            self.assertTrue(task.shell_proxy.env_is_installed())
            task.shell_proxy.uninstall_env()
            # dispatched the message as the uninstall env notify a message
            task_runner.force_dispatch_waiting_messages()
            self.assertFalse(task.shell_proxy.env_is_installed())
        except Exception as exception:
            task: CondaEnvTaskTester = task_runner.get_task()
            if task:
                task.shell_proxy.uninstall_env()
                task_runner.force_dispatch_waiting_messages()
            raise exception

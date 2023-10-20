# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from typing import Type
from unittest import TestCase

from gws_core import (CondaEnvTask, ConfigParams, File, OutputSpec,
                      OutputSpecs, TaskInputs, TaskOutputs, task_decorator)
from gws_core.impl.shell.base_env_shell import BaseEnvShell
from gws_core.impl.shell.base_env_shell_task import BaseEnvShellTask
from gws_core.impl.shell.conda_shell_proxy import CondaShellProxy
from gws_core.impl.shell.mamba_env_task import MambaEnvTask
from gws_core.impl.shell.mamba_shell_proxy import MambaShellProxy
from gws_core.impl.shell.pip_env_task import PipEnvTask
from gws_core.impl.shell.pip_shell_proxy import PipShellProxy
from gws_core.impl.shell.shell_proxy import ShellProxy
from gws_core.task.task_runner import TaskRunner

__cdir__ = os.path.dirname(os.path.realpath(__file__))


# test_env_task
@task_decorator("CondaEnvTaskTester")
class CondaEnvTaskTester(CondaEnvTask):
    output_specs = OutputSpecs({'file': OutputSpec(File)})
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


@task_decorator("MambaEnvTaskTester")
class MambaEnvTaskTester(MambaEnvTask):
    output_specs = OutputSpecs({'file': OutputSpec(File)})
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


@task_decorator("PipEnvTaskTester")
class PipEnvTaskTester(PipEnvTask):
    output_specs = OutputSpecs({'file': OutputSpec(File)})
    env_file_path = os.path.join(__cdir__, "penv", "env_jwt_pip.txt")

    def run_with_proxy(self, params: ConfigParams, inputs: TaskInputs, shell_proxy: PipShellProxy) -> TaskOutputs:
        command = ["python", os.path.join(
            __cdir__, "penv", "jwt_encode.py"), ">", "out.txt"]
        shell_proxy.run(command, shell_mode=True)

        # retrieve the result
        file = File(path=os.path.join(self.working_dir, "out.txt"))
        return {"file": file}


# test_env_task
class TestEnvTask(TestCase):

    def test_conda(self):
        self._test(CondaEnvTaskTester, CondaShellProxy)

    def test_mamba(self):
        self._test(MambaEnvTaskTester, MambaShellProxy)

    def test_pipenv(self):
        self._test(PipEnvTaskTester, PipShellProxy)

    def _test(self, task_type: Type[BaseEnvShellTask], shell_proxy_type: Type[ShellProxy]):
        task_runner = TaskRunner(task_type)

        try:
            output = task_runner.run()

            file: File = output["file"]

            value = file.read().strip()
            self.assertIsNotNone(value)
            self.assertTrue(len(value) > 0)

            task: task_type = task_runner.get_task()

            shell_proxy: BaseEnvShell = task.shell_proxy
            self.assertIsInstance(shell_proxy, shell_proxy_type)
            self.assertTrue(shell_proxy.env_is_installed())
            shell_proxy.uninstall_env()
            # dispatched the message as the uninstall env notify a message
            task_runner.force_dispatch_waiting_messages()
            self.assertFalse(shell_proxy.env_is_installed())
        except Exception as exception:
            task: task_type = task_runner.get_task()
            if task:
                shell_proxy: BaseEnvShell = task.shell_proxy
                shell_proxy.uninstall_env()
                task_runner.force_dispatch_waiting_messages()
            raise exception

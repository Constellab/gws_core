# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import shlex
from abc import abstractmethod
from typing import final

from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher

from ...config.config_types import ConfigParams
from ...task.task import Task
from ...task.task_decorator import task_decorator
from ...task.task_io import TaskInputs, TaskOutputs
from .shell_proxy import ShellProxy


@task_decorator("ShellTask", hide=True)
class ShellTask(Task):
    """
    Shell task.

    This class is a proxy to run user shell commands through the Python method `subprocess.run`.
    """

    input_specs = {}
    output_specs = {}
    config_specs = {}

    shell_proxy: ShellProxy = None

    def __init__(self, message_dispatcher: MessageDispatcher):
        super().__init__(message_dispatcher)
        self.shell_proxy = self.init_shell_proxy()

    def init_shell_proxy(self) -> ShellProxy:
        """
        Initialize the shell proxy
        """

        return ShellProxy(message_dispatcher=self.message_dispatcher)

    @final
    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        return await self.run_with_proxy(params, inputs, self.shell_proxy)

    @abstractmethod
    async def run_with_proxy(self, params: ConfigParams, inputs: TaskInputs,
                             shell_proxy: ShellProxy) -> TaskOutputs:
        """
        Run the task with the shell proxy
        """

    async def run_after_task(self) -> None:
        """
        This can be overwritten to perform action after the task run. This method is called after the
        resource save. Temp object can be safely deleted here, the resources will still exist
        """

        self._clean_working_dir()

    @final
    @property
    def working_dir(self) -> str:
        """
        Returns the working dir of the shell task

        :return: The working dir oif the shell task
        :rtype: `srt`
        """

        return self.shell_proxy.working_dir

    def _clean_working_dir(self):
        """
        Clean the working dir
        """

        self.shell_proxy.clean_working_dir()

    @staticmethod
    def quote(string: str) -> str:
        """
        Return a shell-escaped version of the string (using native python function `shlex.quote()`).
        The returned value is a string that can safely be used as one token in a shell command line,
        for cases where you cannot use a list.
        """
        return shlex.quote(string)

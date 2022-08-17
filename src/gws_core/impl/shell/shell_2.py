# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import shlex
import shutil
from abc import abstractmethod

from gws_core.impl.shell.shell_proxy import ShellProxy

from ...config.config_types import ConfigParams
from ...core.utils.settings import Settings
from ...task.task import Task
from ...task.task_decorator import task_decorator
from ...task.task_io import TaskInputs, TaskOutputs
from ..file.file_helper import FileHelper


@task_decorator("Shell2", hide=True)
class Shell2(Task):
    """
    Shell task.

    This class is a proxy to run user shell commands through the Python method `subprocess.run`.
    """

    input_specs = {}
    output_specs = {}
    config_specs = {}

    _tmp_dir: str = None

    shell_proxy: ShellProxy = None

    def __init__(self):
        super().__init__()
        self.shell_proxy = ShellProxy(self.working_dir)

        # attach this task to the proxy log the output into the progress bar
        self.shell_proxy.attach_task(self)

    @abstractmethod
    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        """This must be overiwritten to perform the task of the task.

        This is where most of your code must go

        :param params: [description]
        :type params: Config
        :param inputs: [description]
        :type inputs: Input
        :param outputs: [description]
        :type outputs: Output
        """

    async def run_after_task(self) -> None:
        """
        This can be overwritten to perform action after the task run. This method is called after the
        resource save. Temp object can be safely deleted here, the resources will still exist
        """

        self._clean_working_dir()

    @property
    def working_dir(self) -> str:
        """
        Returns the working dir of the shell task

        :return: The working dir oif the shell task
        :rtype: `srt`
        """

        if self._tmp_dir is None:
            settings = Settings.retrieve()
            self._tmp_dir = settings.make_temp_dir()

        return self._tmp_dir

    def _clean_working_dir(self):
        """
        Clean the working dir
        """

        if self._tmp_dir is not None:
            FileHelper.delete_dir(self._tmp_dir)
        self._tmp_dir = None

    @staticmethod
    def quote(string: str) -> str:
        """
        Return a shell-escaped version of the string (using native python function `shlex.quote()`).
        The returned value is a string that can safely be used as one token in a shell command line,
        for cases where you cannot use a list.
        """
        return shlex.quote(string)

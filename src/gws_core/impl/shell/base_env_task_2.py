# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from abc import abstractmethod

from ...config.config_types import ConfigParams
from ...core.utils.settings import Settings
from ...task.task import Task
from ...task.task_decorator import task_decorator
from ...task.task_io import TaskInputs, TaskOutputs
from ..file.file_helper import FileHelper
from .base_env import BaseEnv


@task_decorator("BaseEnvShell2", hide=True)
class BaseEnvShell2(Task):
    """
    EnvShell task.

    This class is a proxy to run user shell commands in virtual environments

    :property unique_env_name: The unique name of the virtual environment.
        If `None`, a unique name is automtically defined for the Task.
        The share virtual environments across diffrent task,
        it is recommended to set (freeze) the ```unique_env_name``` in a base class and let other
        compatible tasks inherit this base class.
    :type unique_env_name: `str`
    """

    unique_env_name = None

    shell_proxy: BaseEnv = None
    _tmp_dir: str = None

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

    @classmethod
    def get_env_dir_name(cls) -> str:
        """
        Returns the directory of the virtual env of the task class
        """

        if not cls.unique_env_name:
            cls.unique_env_name = cls.full_classname()

        return cls.unique_env_name

    def env_is_installed(self) -> bool:
        """
        Returns True if the virtual env is installed. False otherwise
        """

        return self.shell_proxy.is_installed()

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

# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from abc import abstractmethod

from ...config.config_types import ConfigParams
from ...task.task_decorator import task_decorator
from ...task.task_io import TaskInputs, TaskOutputs
from .shell_proxy import ShellProxy
from .shell_task import ShellTask


@task_decorator("BaseEnvShellTask", hide=True)
class BaseEnvShellTask(ShellTask):
    """
    EnvShell task.

    This class is a proxy to run user shell commands in virtual environments
    """

    unique_env_name = None
    """ The unique name of the virtual environment.
        If `None`, a unique name is automtically defined for the Task.
        To share virtual environments across diffrent task,
        it is recommended to set (freeze) the ```unique_env_name``` in a base class and let other
        compatible tasks inherit this base class.
    """

    @abstractmethod
    def runproxy(self, params: ConfigParams, inputs: TaskInputs,
                 shell_proxy: ShellProxy) -> TaskOutputs:
        """
        Run the task with the shell proxy
        """

    @classmethod
    def get_env_dir_name(cls) -> str:
        """
        Returns the directory of the virtual env of the task class
        """

        if not cls.unique_env_name:
            cls.unique_env_name = cls._typing_name

        return cls.unique_env_name

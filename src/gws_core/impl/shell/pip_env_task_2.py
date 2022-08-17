# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from abc import abstractmethod

from gws_core.impl.shell.pip_env import PipEnv

from ...config.config_types import ConfigParams
from ...task.task_decorator import task_decorator
from ...task.task_io import TaskInputs, TaskOutputs
from .base_env_task_2 import BaseEnvShell2


@task_decorator("PipEnvShell2", hide=True)
class PipEnvShell2(BaseEnvShell2):
    """
    PipEnvShell task.

    This class allows to run python scripts in pipenv virtual environments. It rely on the awesome
    Pipenv module to efficiently automate the management of your venvs.
    See also https://pipenv.pypa.io/.

    :property env_file_path: The dependencies to install. Could be a list of modules or the path of a dependency file.
    :type env_file_path: `list`,`str`

    * A typical environment Pipefile is:
        ```
        [[source]]
        url = 'https://pypi.python.org/simple'
        verify_ssl = true
        name = 'pypi'

        [requires]
        python_version = '3.8'

        [packages]
        requests = { extras = ['socks'] }
        records = '>0.5.0'
        django = { git = 'https://github.com/django/django.git', ref = '1.11.4', editable = true }
        ```
    """

    # must be overrided in the child class to provide the yml env file path
    env_file_path: str

    shell_proxy: PipEnv = None

    def __init__(self):
        super().__init__()

        if self.env_file_path is None:
            raise Exception(f"The env_file_path property must be set in the task {self._typing_name}")
        self.shell_proxy = PipEnv(self.get_env_dir_name(), self.env_file_path, self.working_dir)
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

# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from abc import abstractmethod

from gws_core.impl.shell.conda_env import CondaEnv

from ...config.config_types import ConfigParams
from ...task.task_decorator import task_decorator
from ...task.task_io import TaskInputs, TaskOutputs
from .base_env_task_2 import BaseEnvShell2


@task_decorator("CondaEnvShell2", hide=True)
class CondaEnvShell2(BaseEnvShell2):
    """
    CondaEnvShell task.

    This class allows to run python scripts in conda virtual environments. It rely on the awesome
    Conda containerization system to efficiently automate the management of your venvs.
    See also https://conda.io/.

    :property env_file_path: The dependencies to install. Could be a list of modules or the path of a dependency file.
    :type env_file_path: `list`,`str`

    For conda, a typical yml environment file content is:
        ```
        name: my_env_name
        channels:
          - javascript
          - conda-forge
        dependencies:
          - r-base=3.1.2
          - r-tidyverse
          - python=3.6
          - bokeh=0.9.2
          - numpy=1.9.*
          - nodejs=0.10.*
          - flask
          - pip:
            - Flask-Testing
        ```
    """

    # must be overrided in the child class to provide the yml env file path
    env_file_path: str

    shell_proxy: CondaEnv = None

    def __init__(self):
        super().__init__()

        if self.env_file_path is None:
            raise Exception(f"The env_file_path property must be set in the task {self._typing_name}")

        self.shell_proxy = CondaEnv(self.get_env_dir_name(), self.env_file_path, self.working_dir)
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

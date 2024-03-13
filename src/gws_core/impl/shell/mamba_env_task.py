

from abc import abstractmethod

from gws_core.impl.shell.mamba_shell_proxy import MambaShellProxy

from ...config.config_params import ConfigParams
from ...task.task_decorator import task_decorator
from ...task.task_io import TaskInputs, TaskOutputs
from .base_env_shell_task import BaseEnvShellTask
from .shell_proxy import ShellProxy


@task_decorator("MambaEnvTask", hide=True)
class MambaEnvTask(BaseEnvShellTask):
    """
    MambaEnvTask task.

    This class allows to run python scripts in mamba virtual environments. It rely on the awesome
    Mamba containerization system to efficiently automate the management of your venvs.
    See also https://conda.io/.

    :property env_file_path: The dependencies to install. Could be a list of modules or the path of a dependency file.
    :type env_file_path: `list`,`str`

    For mamba, a typical yml environment file content is (same as conda):
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

    shell_proxy: MambaShellProxy = None

    def init(self) -> None:
        if self.env_file_path is None:
            raise Exception(f"The env_file_path property must be set in the task {self._typing_name}")
        super().init()

    def init_shell_proxy(self) -> ShellProxy:
        return MambaShellProxy(self.get_env_dir_name(), env_file_path=self.env_file_path,
                               message_dispatcher=self.message_dispatcher)

    @abstractmethod
    def run_with_proxy(self, params: ConfigParams, inputs: TaskInputs, shell_proxy: MambaShellProxy) -> TaskOutputs:
        """
        Run the task with the shell proxy
        """

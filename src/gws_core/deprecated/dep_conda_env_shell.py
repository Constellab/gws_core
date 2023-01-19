# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from abc import abstractmethod

from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher

from ..config.config_types import ConfigParams
from ..impl.shell.conda_shell_proxy import CondaShellProxy
from ..task.task_decorator import task_decorator
from ..task.task_io import TaskInputs, TaskOutputs
from .dep_base_env_task import DepBaseEnvShell


@task_decorator("CondaEnvShell", hide=True, deprecated_since="0.3.16",
                deprecated_message="Use new CondaShellTask instead")
class CondaEnvShell(DepBaseEnvShell):
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

    env_file_path: str = None
    _shell_mode = True

    def __init__(self, message_dispatcher: MessageDispatcher):
        super().__init__(message_dispatcher)
        self.base_env = CondaShellProxy(self.get_env_dir_name(), self.env_file_path, self.working_dir)

    @abstractmethod
    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        """
        This methods gathers the results of the shell task. It must be overloaded by subclasses.

        It must be overloaded to capture the standard output (stdout) and the
        output files generated in the current working directory (see `gws.Shell.cwd`)

        :param stdout: The standard output of the shell task
        :type stdout: `str`
        """

# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from abc import abstractmethod

from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.impl.shell.pip_shell_proxy import PipShellProxy

from ..config.config_types import ConfigParams
from ..task.task_decorator import task_decorator
from ..task.task_io import TaskInputs, TaskOutputs
from .dep_base_env_task import DepBaseEnvShell


@task_decorator("PipEnvShell", hide=True, deprecated_since="0.3.16", deprecated_message="Use PipEnvTask instead")
class PipEnvShell(DepBaseEnvShell):
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

    env_file_path: str
    base_env: PipShellProxy = None
    _shell_mode = True

    def __init__(self, message_dispatcher: MessageDispatcher):
        super().__init__(message_dispatcher)
        self.base_env = PipShellProxy(self.get_env_dir_name(), self.env_file_path, self.working_dir)

    @abstractmethod
    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        """
        This methods gathers the results of the shell task. It must be overloaded by subclasses.

        It must be overloaded to capture the standard output (stdout) and the
        output files generated in the current working directory (see `gws.Shell.cwd`)

        :param stdout: The standard output of the shell task
        :type stdout: `str`
        """

    async def run_after_task(self) -> None:
        await super().run_after_task()
        self.uninstall()



from abc import abstractmethod

from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher

from ...config.config_params import ConfigParams
from ...task.task_decorator import task_decorator
from ...task.task_io import TaskInputs, TaskOutputs
from .base_env_shell_task import BaseEnvShellTask
from .pip_shell_proxy import PipShellProxy
from .shell_proxy import ShellProxy


@task_decorator("PipEnvTask", hide=True)
class PipEnvTask(BaseEnvShellTask):
    """
    PipEnvTask task.

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
        python_version = '3.10'

        [packages]
        requests = { extras = ['socks'] }
        records = '>0.5.0'
        django = { git = 'https://github.com/django/django.git', ref = '1.11.4', editable = true }
        ```
    """

    # must be overrided in the child class to provide the yml env file path
    env_file_path: str

    shell_proxy: PipShellProxy = None

    def init(self) -> None:
        if self.env_file_path is None:
            raise Exception(f"The env_file_path property must be set in the task {self._typing_name}")
        super().init()

    def init_shell_proxy(self) -> ShellProxy:
        return PipShellProxy(
            self.get_env_dir_name(),
            env_file_path=self.env_file_path, message_dispatcher=self.message_dispatcher)

    @abstractmethod
    def run_with_proxy(self, params: ConfigParams, inputs: TaskInputs, shell_proxy: PipShellProxy) -> TaskOutputs:
        """
        Run the task with the shell proxy
        """

# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.config.param.code_param.python_code_param import PythonCodeParam
from gws_core.config.param.code_param.r_code_param import RCodeParam
from gws_core.impl.live.base.env_live_task import EnvLiveTask
from gws_core.impl.live.helper.live_code_helper import LiveCodeHelper
from gws_core.impl.shell.conda_shell_proxy import CondaShellProxy

from ...config.config_types import ConfigSpecs
from ...task.task_decorator import task_decorator


@task_decorator(
    "RCondaLiveTask", human_name="R live task for conda shell",
    short_description="Live task to run R snippets in conda a shell environment. The inputs files are passed to the snippet through the arguments.")
class RCondaLiveTask(EnvLiveTask):
    """
    Conda-based R live tasks allow to execute R snippets on the fly in isolated conda environments.

    Live tasks are fast and efficient tools to develop, test, use and share code snippets.

    Conda is a tool to automatically creates and manages a virtualenv for your projects.
    Confgure you R environment using a YAML data and enjoy!

    See also https://https://docs.conda.io/, https://www.r-project.org/

    > **Warning**: It is recommended to use code snippets comming from trusted sources.
    """

    SNIPPET_FILE_EXTENSION: str = "R"

    config_specs: ConfigSpecs = {
        'params': EnvLiveTask.get_list_param_config(),
        'env': PythonCodeParam(
            default_value=LiveCodeHelper.get_r_conda_env_file_template(),
            human_name="YAML configurtation", short_description="YAML configuration of the R conda environment"
        ),
        'code': RCodeParam(
            default_value=LiveCodeHelper.get_r_template(),
            human_name="R code snippet", short_description="The R code snippet to execute using shell command"),
    }

    def _format_command(self, code_file_path: str) -> list:
        return ["Rscript", code_file_path]

    def _create_shell_proxy(self, env: str) -> CondaShellProxy:
        return CondaShellProxy.from_env_str(env, message_dispatcher=self.message_dispatcher)

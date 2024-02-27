# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core.config.param.code_param.python_code_param import PythonCodeParam
from gws_core.impl.live.base.env_live_task import EnvLiveTask
from gws_core.impl.live.helper.live_code_helper import LiveCodeHelper
from gws_core.impl.shell.pip_shell_proxy import PipShellProxy

from ...config.config_types import ConfigSpecs
from ...task.task_decorator import task_decorator


@task_decorator(
    "PyPipenvLiveTask", human_name="Pip env live task",
    short_description="Live task to run Python snippets in a pipenv shell environment.",
    icon="code")
class PyPipenvLiveTask(EnvLiveTask):
    """
    Pipenv-based Python live tasks allow to execute Python snippets on the fly in isolated Pipenv environments.

    Live tasks are fast and efficient tools to develop, test, use and share code snippets.

    **Warning**: It is recommended to use code snippets comming from trusted sources.

    Here is the general documentation for live task (including how to use the parameters): https://constellab.community/bricks/gws_core/latest/doc/developer-guide/live-task/getting-started

    Here is the documentation of the live task: https://constellab.community/bricks/gws_core/latest/doc/developer-guide/live-task/env-live-task
    """

    SNIPPET_FILE_EXTENSION: str = "py"

    config_specs: ConfigSpecs = {
        'params': EnvLiveTask.get_list_param_config(),
        'env': PythonCodeParam(
            default_value=LiveCodeHelper.get_pip_env_file_template(),
            human_name="Pipenv configuration", short_description="Pipenv configuration"
        ),
        'code': PythonCodeParam(
            default_value=LiveCodeHelper.get_python_with_env_template(),
            human_name="Code snippet", short_description="The code snippet to execute using shell command"),
    }

    def _format_command(self, code_file_path: str) -> list:
        return ["python", code_file_path]

    def _create_shell_proxy(self, env: str) -> PipShellProxy:
        return PipShellProxy.from_env_str(env, message_dispatcher=self.message_dispatcher)

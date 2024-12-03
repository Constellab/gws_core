

from gws_core.config.param.code_param.python_code_param import PythonCodeParam
from gws_core.impl.live.base.env_agent import EnvAgent
from gws_core.impl.live.helper.live_code_helper import LiveCodeHelper
from gws_core.impl.shell.pip_shell_proxy import PipShellProxy
from gws_core.model.typing_style import TypingStyle

from ...config.config_types import ConfigSpecs
from ...task.task_decorator import task_decorator


@task_decorator(
    "PyPipenvAgent", human_name="Pip env agent",
    short_description="Agent to run Python snippets in a pipenv shell environment.",
    style=TypingStyle.material_icon("code"))
class PyPipenvAgent(EnvAgent):
    """
    Pipenv-based Python agents allow to execute Python snippets on the fly in isolated Pipenv environments.

    Agents are fast and efficient tools to develop, test, use and share code snippets.

    **Warning**: It is recommended to use code snippets comming from trusted sources.

    Here is the general documentation for agent (including how to use the parameters): https://constellab.community/bricks/gws_core/latest/doc/developer-guide/agent/getting-started/69820653-52e0-41ba-a5f3-4d9d54561779

    Here is the documentation of the agent: https://constellab.community/bricks/gws_core/latest/doc/developer-guide/agent/env-agent/c6acb3c3-2a7c-44cd-8fb2-ea1beccdbdcc
    """

    SNIPPET_FILE_EXTENSION: str = "py"

    config_specs: ConfigSpecs = {
        'params': EnvAgent.get_dynamic_param_config(),
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

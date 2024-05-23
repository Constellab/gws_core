

from typing import List

from gws_core.config.param.code_param.r_code_param import RCodeParam
from gws_core.config.param.code_param.yaml_code_param import YamlCodeParam
from gws_core.impl.live.base.env_live_task import EnvLiveTask
from gws_core.impl.live.helper.live_code_helper import LiveCodeHelper
from gws_core.impl.shell.conda_shell_proxy import CondaShellProxy
from gws_core.model.typing_style import TypingStyle

from ...config.config_types import ConfigSpecs
from ...task.task_decorator import task_decorator


@task_decorator(
    "RCondaLiveTask", human_name="R conda env live task",
    short_description="Live task to run R snippets in conda a shell environment.",
    style=TypingStyle.material_icon("code"))
class RCondaLiveTask(EnvLiveTask):
    """
    Conda-based R live tasks allow to execute R snippets on the fly in isolated conda environments.

    Live tasks are fast and efficient tools to develop, test, use and share code snippets.

    **Warning**: It is recommended to use code snippets comming from trusted sources.

    Here is the general documentation for live task (including how to use the parameters): https://constellab.community/bricks/gws_core/latest/doc/developer-guide/live-task/getting-started/69820653-52e0-41ba-a5f3-4d9d54561779

    Here is the documentation of the live task: https://constellab.community/bricks/gws_core/latest/doc/developer-guide/live-task/env-live-task/c6acb3c3-2a7c-44cd-8fb2-ea1beccdbdcc
    """

    SNIPPET_FILE_EXTENSION: str = "R"

    config_specs: ConfigSpecs = {
        'params': EnvLiveTask.get_list_param_config(),
        'env': YamlCodeParam(
            default_value=LiveCodeHelper.get_r_conda_env_file_template(),
            human_name="Conda environment (YAML)", short_description="YAML configuration of the R conda environment"
        ),
        'code': RCodeParam(
            default_value=LiveCodeHelper.get_r_template(),
            human_name="R code snippet", short_description="The R code snippet to execute using shell command"),
    }

    def _format_command(self, code_file_path: str) -> list:
        return ["Rscript", code_file_path]

    def _get_init_code(self, source_paths_var_name: str,
                       source_paths: List[str], target_paths_var_name: str) -> str:
        source_value = [f"\'{p}\'" for p in source_paths]
        source_value_str = f'c({",".join(source_value)})'
        # using python and json package, write the target paths to a file
        return f"""{source_paths_var_name} <- {source_value_str}
{target_paths_var_name} <- list()"""

    def _get_write_target_paths_code(self, target_paths_var_name: str, target_paths_filename: str) -> str:
        # convert the above to R code
        return f"""# convert the target paths to a json string
json_data <- paste0("[", paste0('"', {target_paths_var_name}, '"', collapse = ","), "]")
# write the json string to a file
write(json_data, file = "{target_paths_filename}")"""

    def _create_shell_proxy(self, env: str) -> CondaShellProxy:
        return CondaShellProxy.from_env_str(env, message_dispatcher=self.message_dispatcher)

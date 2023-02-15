# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core.config.param.code_param.python_code_param import PythonCodeParam

from ...config.config_types import ConfigSpecs
from ...config.param.param_spec import ListParam, StrParam
from ...task.task_decorator import task_decorator
from .base.conda_live_task import CondaLiveTask
from .helper.template_reader_helper import TemplateReaderHelper


@task_decorator(
    "RCondaLiveTask", human_name="R live task for conda shell",
    short_description="Live task to run R snippets in conda a shell environment. The inputs files are passed to the snippet through the arguments.")
class RCondaLiveTask(CondaLiveTask):
    """
    Conda-based R live tasks allow to execute R snippets on the fly in isolated conda environments.

    Live tasks are fast and efficient tools to develop, test, use and share code snippets.

    Conda is a tool to automatically creates and manages a virtualenv for your projects.
    Confgure you R environment using a YAML data and enjoy!

    See also https://https://docs.conda.io/, https://www.r-project.org/

    > **Warning**: It is recommended to use code snippets comming from trusted sources.
    """

    SNIPPET_FILE_EXTENSION: str = ".R"

    config_specs: ConfigSpecs = {
        'env': PythonCodeParam(
            default_value=TemplateReaderHelper.read_env_config_template(file_name="env_r_conda.yml"),
            human_name="YAML configurtation", short_description="YAML configuration of the R conda environment"
        ),
        'args':
        StrParam(
            optional=True, default_value="", human_name="Shell arguments",
            short_description="Shell arguments used to call the script. For example: Use '--datapath {input:*}' to pass a single input `File`. Use '--datapath1 {input:file1} --datapath2 {input:file2}' to pass several files from an input `ResourceSet`."),
        'output_file_paths':
        ListParam(
            human_name="Output file paths",
            short_description="The paths of the files to capture in the outputs. For example: Enter 'result.csv' to capture this file in the outputs. Please ensure that this file is created by the script"),
        'code': PythonCodeParam(
            default_value=TemplateReaderHelper.read_snippet_template(file_name="r_env_snippet_template.R"),
            human_name="R code snippet", short_description="The R code snippet to execute using shell command"),
    }

    def _format_command(self, code_file_path: str, args: str) -> list:
        return ["Rscript", code_file_path, args]

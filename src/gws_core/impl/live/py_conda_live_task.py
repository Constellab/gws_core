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
    "PyCondaLiveTask", human_name="Python live task for conda shell",
    short_description="Live task to run Python snippets in a conda shell environment. The inputs files are passed to the snippet through the arguments.")
class PyCondaLiveTask(CondaLiveTask):
    """
    Conda-based Python live tasks allow to execute Python snippets on the fly in isolated conda environments.

    Live tasks are fast and efficient tools to develop, test, use and share code snippets.

    Conda is a tool to automatically creates and manages a virtualenv for your projects.

    See also https://https://docs.conda.io/

    > **Warning**: It is recommended to use code snippets comming from trusted sources.
    """

    SNIPPET_FILE_EXTENSION: str = ".py"

    config_specs: ConfigSpecs = {
        'env': PythonCodeParam(
            default_value=TemplateReaderHelper.read_env_config_template(file_name="env_py_conda.yml"),
            human_name="YAML configurtation", short_description="YAML configuration of the conda environment"
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
            default_value=TemplateReaderHelper.read_snippet_template(file_name="py_env_snippet_template.py"),
            human_name="Python code snippet", short_description="The Python code snippet to execute using shell command"),
    }

    def _format_command(self, code_file_path: str, args: str) -> list:
        return ["python", code_file_path, args]

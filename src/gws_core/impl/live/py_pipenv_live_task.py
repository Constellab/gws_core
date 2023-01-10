# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core.config.param.code_param.python_code_param import PythonCodeParam

from ...config.config_types import ConfigSpecs
from ...config.param.param_spec import ListParam, StrParam
from ...task.task_decorator import task_decorator
from .base.pipenv_live_task import PipenvLiveTask
from .helper.template_reader_helper import TemplateReaderHelper


@task_decorator(
    "PyPipenvLiveTask", human_name="Python live task for pipenv shell",
    short_description="Live task to run Python snippets in a pipenv shell environment. The inputs files are passed to the snippet through the arguments.")
class PyPipenvLiveTask(PipenvLiveTask):
    """
    Pipenv-based Python live tasks allow to execute Python snippets on the fly in isolated Pipenv environments.

    Live tasks are fast and efficient tools to develop, test, use and share code snippets.

    Pipenv is a tool to automatically creates and manages a virtualenv for your projects.

    See also https://pipenv.pypa.io/

    > **Warning**: It is recommended to use code snippets comming from trusted sources.
    """

    SNIPPET_FILE_EXTENSION: str = ".py"

    config_specs: ConfigSpecs = {
        'env': PythonCodeParam(
            default_value=TemplateReaderHelper.read_env_config_template(file_name="env_pipenv.txt"),
            human_name="Pipenv configuration", short_description="Pipenv configuration"
        ),
        'args':
        StrParam(
            optional=True, default_value="", human_name="Shell arguments",
            short_description="Shell arguments used to call the script. Use wildcards {input:*} to pass the input files to the script. For example: '--data1 {input:filename_1} --data2 {input:filename_2} -o out_file.txt'."),
        'output_file_paths':
        ListParam(
            human_name="Output file paths",
            short_description="The paths of the files to capture in the outputs. For example: Enter 'out_file.txt' to capture this file in the outputs"),
        'code': PythonCodeParam(
            default_value=TemplateReaderHelper.read_snippet_template(file_name="py_env_snippet_template.py"),
            human_name="Code snippet", short_description="The code snippet to execute using shell command"),
    }

    def _format_command(self, code_file_path: str, args: str) -> list:
        return ["python", code_file_path, args]

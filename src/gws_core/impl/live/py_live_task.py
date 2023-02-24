# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import runpy
import tempfile

from gws_core.config.param.code_param.python_code_param import PythonCodeParam

from ...config.config_types import ConfigParams, ConfigSpecs
from ...config.param.param_spec import ListParam
from ...core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ...io.io_spec import InputSpec, OutputSpec
from ...io.io_spec_helper import InputSpecs, OutputSpecs
from ...resource.resource import Resource
from ...task.task import Task
from ...task.task_decorator import task_decorator
from ...task.task_io import TaskInputs, TaskOutputs
from .helper.template_reader_helper import TemplateReaderHelper


@task_decorator("PyLiveTask", human_name="Python live task",
                short_description="Live task to run Python snippets directly in the global environment. The input data and parameters are passed in memory to the snippet.")
class PyLiveTask(Task):
    """
    Python live tasks allow to execute any Python code snippets on the fly.

    Live tasks are fast and efficient tools to develop, test, use and share code snippets.

    > **Warning**: It is recommended to use code snippets comming from trusted sources.
    """

    input_specs: InputSpecs = {
        'source': InputSpec(Resource, is_optional=True),
    }
    output_specs: OutputSpecs = {
        'target': OutputSpec(Resource, sub_class=True, is_optional=True),
    }
    config_specs: ConfigSpecs = {
        'params':
        ListParam(
            optional=True, default_value=[],
            human_name="Parameter definitions",
            short_description="Please give one parameter definition per line"),
        'code':
        PythonCodeParam(
            default_value=TemplateReaderHelper.read_snippet_template(file_name="py_live_snippet_template.py"),
            human_name="Python code snippet",
            short_description="Python code snippet to run"), }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        code: str = params.get_value('code')
        params = params.get_value('params')

        _, snippet_filepath = tempfile.mkstemp(suffix=".py")
        with open(snippet_filepath, 'w', encoding="utf-8") as fp:
            params_str: str = "\n".join(params)
            fp.write(code)

        # compute params
        param_context = {}
        if params:
            params_str: str = "\n".join(params)
            try:
                exec(params_str, {}, param_context)
            except Exception as err:
                raise BadRequestException("Cannot parse parameters") from err

        # execute the live code
        init_globals = {'self': self, "inputs": inputs, "params": param_context, **globals()}
        global_vars = runpy.run_path(snippet_filepath, init_globals=init_globals)
        outputs = global_vars.get("outputs", None)

        if outputs is not None:
            if not isinstance(outputs, dict):
                raise BadRequestException("The outputs must be a dictionary")

            if 'target' not in outputs:
                raise BadRequestException("The outputs must have single key 'target'")

        return outputs

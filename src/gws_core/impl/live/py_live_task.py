# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core.config.param.python_code_param import PythonCodeParam

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


@task_decorator("PyLiveTask", human_name="Python live task",
                short_description="Live task to run Python snippets directly in the global environment. The input data and parameters are passed in memory to the snippet.")
class PyLiveTask(Task):
    """
    This task executes python code snippets on the fly.

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
            human_name="Parameters", short_description="The parameters"),
        'code': PythonCodeParam(human_name="Python code snippet", short_description="Python code snippet to run"), }

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        code: str = params.get_value('code')
        params = params.get_value('params')

        # compute params
        param_context = {}
        if params:
            params_str: str = "\n".join(params)
            try:
                exec(params_str, {}, param_context)
            except Exception as err:
                raise BadRequestException("Cannot parse parameters") from err

        # execute the live code
        global_vars = globals()
        local_vars = {'self': self, "inputs": inputs, "params": param_context}

        try:
            exec(code, global_vars, local_vars)
        except Exception as err:
            raise BadRequestException(f"An error occured during the excution of the live code. Error: {err}") from err

        outputs = local_vars.get("outputs", None)

        if outputs is not None:
            if not isinstance(outputs, dict):
                raise BadRequestException("The outputs must be a dictionary")

        return outputs

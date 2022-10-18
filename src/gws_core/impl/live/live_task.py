# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import re

from gws_core import BadRequestException, ListParam, StrParam

from ...config.config_types import ConfigParams, ConfigSpecs
from ...io.io_spec import InputSpec, OutputSpec
from ...io.io_spec_helper import InputSpecs, OutputSpecs
from ...resource.resource import Resource
from ...task.task import Task
from ...task.task_decorator import task_decorator
from ...task.task_io import TaskInputs, TaskOutputs


@task_decorator("LiveTask", human_name="Live task", short_description="Low-code live task")
class LiveTask(Task):
    """
    Live task for low-code implementation
    """

    input_specs: InputSpecs = {
        'source': InputSpec(Resource, is_optional=True),
    }
    output_specs: OutputSpecs = {
        'target': OutputSpec(Resource, is_optional=True),
    }
    config_specs: ConfigSpecs = {
        'code': ListParam(human_name="Code", short_description="The code text"),
        'params': ListParam(optional=True, default_value=[], human_name="Parameters", short_description="The parameters"),
        'language': StrParam(allowed_values=['python'], default_value='python', human_name="Language", short_description="The code language"),
        'pip_packages': ListParam(optional=True, default_value=[], visibility=ListParam.PROTECTED_VISIBILITY, human_name="PIP packages", short_description="PIP packages"),
    }

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        code: str = params.get_value('code')
        language = params.get_value('language')
        params = params.get_value('params')

        # validate user input, params, code

        if language == "python":
            try:
                # compute params
                param_context = {}
                if params:
                    params_str = "\n".join(params)
                    exec(params_str, {}, param_context)

                # execute code
                global_vars = globals()
                local_vars = {'inputs': inputs, **param_context}
                code = "\n".join(code)
                exec(code, global_vars, local_vars)
                output = local_vars.get("output", None)
            except Exception as err:
                raise BadRequestException(f"An error orccured. Error: {err}") from err
        elif language == "R":
            raise BadRequestException("R language is not yet supported")
        elif language == "bash":
            raise BadRequestException("Bash language is not yet supported")
        else:
            raise BadRequestException("This language is not supported")

        if output is not None:
            if not isinstance(output, Resource):
                raise BadRequestException("The returned output is not a Resource")
            return {"target": output}

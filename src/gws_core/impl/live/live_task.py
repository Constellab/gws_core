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


@task_decorator("LiveTask", human_name="Live task", short_description="Live task")
class LiveTask(Task):
    """
    Task for live code execution.

    This task allows executing python code on the fly.

    > **Warning**: Be careful to use code that you develped yourself or coming from trusted sources.
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
        'code': ListParam(human_name="Code", short_description="The code text"),
    }

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        code: str = params.get_value('code')
        params = params.get_value('params')

        # validate user inputs, params, code
        try:
            # compute params
            param_context = {}
            if params:
                params_str: str = "\n".join(params)
                exec(params_str, {}, param_context)

            # execute the live code
            global_vars = globals()
            local_vars = {'self': self, **inputs, **param_context}
            code: str = "\n".join(code)

            exec(code, global_vars, local_vars)
            target = local_vars.get("target", None)

            return {'target': target}
        except Exception as err:
            raise BadRequestException(f"An error occured during the excution of the live code. Error: {err}") from err

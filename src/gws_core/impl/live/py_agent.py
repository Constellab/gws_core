

from typing import List

from gws_core.config.param.code_param.python_code_param import PythonCodeParam
from gws_core.impl.live.base.env_agent import EnvAgent
from gws_core.impl.live.helper.live_code_helper import LiveCodeHelper
from gws_core.io.dynamic_io import DynamicInputs, DynamicOutputs
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.resource_set.resource_list import ResourceList

from ...config.config_params import ConfigParams
from ...config.config_types import ConfigParamsDict, ConfigSpecs
from ...io.io_specs import InputSpecs, OutputSpecs
from ...task.task import Task
from ...task.task_decorator import task_decorator
from ...task.task_io import TaskInputs, TaskOutputs


@task_decorator("PyAgent", human_name="Python agent",
                short_description="Agent to run Python snippets directly in the global environment. The input data and parameters are passed in memory to the snippet.",
                style=TypingStyle.material_icon("code"))
class PyAgent(Task):
    """
    Python agents allow to execute any Python code snippets on the fly.

    Agents are fast and efficient tools to develop, test, use and share code snippets.

    **Warning**: It is recommended to use code snippets comming from trusted sources.

    Here is the general documentation for agent (including how to use the parameters): https://constellab.community/bricks/gws_core/latest/doc/developer-guide/agent/getting-started/69820653-52e0-41ba-a5f3-4d9d54561779

    Here is the documentation of the agent: https://constellab.community/bricks/gws_core/latest/doc/developer-guide/agent/env-agent/c6acb3c3-2a7c-44cd-8fb2-ea1beccdbdcc
    """

    input_specs: InputSpecs = DynamicInputs()
    output_specs: OutputSpecs = DynamicOutputs()
    config_specs: ConfigSpecs = {
        'params': EnvAgent.get_list_param_config(),
        'code':
        PythonCodeParam(
            default_value=LiveCodeHelper.get_python_template(),
            human_name="Python code snippet",
            short_description="Python code snippet to run"), }

    CONFIG_PARAMS_NAME = 'params'
    CONFIG_CODE_NAME = 'code'

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        code: str = params.get_value('code')
        params = params.get_value('params')

        # convert param to string and leave empty if no params so it does not offset the
        # line number of the code
        str_params = "\n".join(params)
        if len(params) > 0:
            str_params = str_params + "\n"

        # add the params to the code
        code_with_params = f"{str_params}{code}"

        working_dir = self.create_tmp_dir()

        resource_list: ResourceList = inputs.get('source')

        # execute the live code
        init_globals = {'self': self, 'sources': resource_list.get_resources(),
                        "working_dir": working_dir, **globals()}

        result = LiveCodeHelper.run_python_code(code_with_params, init_globals)

        targets = result.get("targets", None)

        if targets is None:
            targets = []

        return {'target': ResourceList(targets)}

    @classmethod
    def build_config_params_dict(cls, code: str, params: List[str]) -> ConfigParamsDict:
        return {'code': code, "params": params}

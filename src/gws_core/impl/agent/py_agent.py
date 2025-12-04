from typing import Any, Dict

from gws_core.config.config_params import ConfigParamsDict
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.code_param.python_code_param import PythonCodeParam
from gws_core.impl.agent.env_agent import EnvAgent
from gws_core.impl.agent.helper.agent_code_helper import AgentCodeHelper
from gws_core.io.dynamic_io import DynamicInputs, DynamicOutputs
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.resource_set.resource_list import ResourceList

from ...config.config_params import ConfigParams
from ...io.io_specs import InputSpecs, OutputSpecs
from ...task.task import Task
from ...task.task_decorator import task_decorator
from ...task.task_io import TaskInputs, TaskOutputs


@task_decorator(
    "PyAgent",
    human_name="Python agent",
    short_description="Agent to run Python snippets directly in the global environment. The input data and parameters are passed in memory to the snippet.",
    style=TypingStyle.material_icon("agent"),
)
class PyAgent(Task):
    """
    Python agents allow to execute any Python code snippets on the fly.

    Agents are fast and efficient tools to develop, test, use and share code snippets.

    **Warning**: It is recommended to use code snippets comming from trusted sources.

    Here is the general documentation for agent: https://constellab.community/bricks/gws_core/latest/doc/developer-guide/agent/getting-started/69820653-52e0-41ba-a5f3-4d9d54561779

    Here is the documentation of the agent: https://constellab.community/bricks/gws_core/latest/doc/developer-guide/agent/env-agent/c6acb3c3-2a7c-44cd-8fb2-ea1beccdbdcc
    """

    input_specs: InputSpecs = DynamicInputs()
    output_specs: OutputSpecs = DynamicOutputs()
    config_specs = ConfigSpecs(
        {
            "params": EnvAgent.get_dynamic_param_config(),
            "code": PythonCodeParam(
                default_value=AgentCodeHelper.get_python_code_template(),
                human_name="Python code snippet",
                short_description="Python code snippet to run",
            ),
        }
    )

    CONFIG_PARAMS_NAME = "params"
    CONFIG_CODE_NAME = "code"

    __is_agent__: bool = True

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        code: str = params.get_value("code")

        working_dir = self.create_tmp_dir()

        resource_list: ResourceList = inputs.get("source")

        # execute the live code
        init_globals = {
            "self": self,
            "sources": resource_list.get_resources(),
            "params": params.get_value("params"),
            "working_dir": working_dir,
            **globals(),
        }

        result = AgentCodeHelper.run_python_code(code, init_globals)

        targets = result.get("targets", None)

        if targets is None:
            targets = []

        return {"target": ResourceList(targets)}

    @classmethod
    def build_config_params_dict(cls, code: str, params: Dict[str, Any]) -> ConfigParamsDict:
        return {"code": code, "params": params}

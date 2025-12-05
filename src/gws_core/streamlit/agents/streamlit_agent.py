from typing import Any

from gws_core.config.config_params import ConfigParams, ConfigParamsDict
from gws_core.config.config_specs import ConfigSpecs
from gws_core.impl.agent.env_agent import EnvAgent
from gws_core.impl.agent.helper.agent_code_helper import AgentCodeHelper
from gws_core.io.dynamic_io import DynamicInputs
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.model.typing_style import TypingIconType
from gws_core.resource.resource import Resource
from gws_core.resource.resource_set.resource_list import ResourceList
from gws_core.streamlit.streamlit_resource import StreamlitResource
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs


@task_decorator(
    "StreamlitAgent",
    human_name="Streamlit agent",
    short_description="Agent to generate a streamlit app dashboard",
    style=StreamlitResource.copy_style(
        icon_technical_name="agent", icon_type=TypingIconType.MATERIAL_ICON
    ),
)
class StreamlitAgent(Task):
    """
    Agent to generate a streamlit app dashboard.

    **Warning**: It is recommended to use code snippets comming from trusted sources.

    Here is the general documentation for agent (including how to use the parameters):
    https://constellab.community/bricks/gws_core/latest/doc/developer-guide/agent/getting-started/69820653-52e0-41ba-a5f3-4d9d54561779

    Here is the documentation of the agent:
    https://constellab.community/bricks/gws_core/latest/doc/developer-guide/agent/env-agent/c6acb3c3-2a7c-44cd-8fb2-ea1beccdbdcc

    More information about streamlit: https://streamlit.io

    If a resource list or set is provided, the resources will be flatten and added to the streamlit app.
    The order of the resources of a resource set will not be kept.
    """

    input_specs: InputSpecs = DynamicInputs(
        additionnal_port_spec=InputSpec(Resource, human_name="Resource", optional=True)
    )
    output_specs: OutputSpecs = OutputSpecs(
        {"streamlit_app": OutputSpec(StreamlitResource, human_name="Streamlit app")}
    )
    config_specs = ConfigSpecs(
        {
            "params": EnvAgent.get_dynamic_param_config(),
            "code": AgentCodeHelper.get_streamlit_code_param(),
            "requires_authentication": AgentCodeHelper.get_streamlit_requires_auth_param(),
        }
    )

    __is_agent__: bool = True

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        # build the streamlit resource with the code and the resources
        streamlit_resource = StreamlitResource()
        streamlit_resource.set_streamlit_code(params.get_value("code"))
        streamlit_resource.set_params(params.get_value("params"))
        resource_list: ResourceList = inputs.get("source")
        streamlit_resource.add_multiple_resources(resource_list.to_list(), self.message_dispatcher)
        streamlit_resource.set_requires_authentication(params.get_value("requires_authentication"))

        return {"streamlit_app": streamlit_resource}

    @classmethod
    def build_config_params_dict(cls, code: str, params: dict[str, Any]) -> ConfigParamsDict:
        return {"code": code, "params": params}


from abc import abstractmethod
from typing import Any, Dict

from gws_core.config.config_params import ConfigParams, ConfigParamsDict
from gws_core.impl.file.fs_node import FSNode
from gws_core.impl.shell.base_env_shell import BaseEnvShell
from gws_core.io.dynamic_io import DynamicInputs
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.model.typing_style import TypingIconType
from gws_core.resource.resource_set.resource_list import ResourceList
from gws_core.streamlit.streamlit_resource import StreamlitResource
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs


@task_decorator("StreamlitEnvAgent", human_name="Streamlit env agent",
                short_description="Agent to generate a streamlit app dashboard in a virtual environment",
                style=StreamlitResource.copy_style(
                    icon_technical_name='agent', icon_type=TypingIconType.MATERIAL_ICON),
                hide=True)
class StreamlitEnvAgent(Task):
    """
    Agent to generate a streamlit app dashboard.

    **Warning**: It is recommended to use code snippets comming from trusted sources.

    Here is the general documentation for agent (including how to use the parameters): https://constellab.community/bricks/gws_core/latest/doc/developer-guide/agent/getting-started/69820653-52e0-41ba-a5f3-4d9d54561779

    Here is the documentation of the agent: https://constellab.community/bricks/gws_core/latest/doc/developer-guide/agent/env-agent/c6acb3c3-2a7c-44cd-8fb2-ea1beccdbdcc

    More information about streamlit: https://streamlit.io

    If a resource list or set is provided, the resources will be flatten and added to the streamlit app.
    The order of the resources of a resource set will not be kept.
    """

    input_specs: InputSpecs = DynamicInputs(
        additionnal_port_spec=InputSpec(FSNode, human_name="File or folder", is_optional=True))
    output_specs: OutputSpecs = OutputSpecs({
        'streamlit_app': OutputSpec(StreamlitResource, human_name="Streamlit app")
    })

    __is_agent__: bool = True

    @abstractmethod
    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        pass

    def run_agent(self, resources: ResourceList, params: Dict[str, Any],
                  code: str,
                  requires_authentication: bool,
                  env_code: str = None,
                  env_shell_proxy: BaseEnvShell = None) -> StreamlitResource:

        if env_code is not None and 'streamlit' not in env_code:
            raise Exception("The env code must contain the 'streamlit' package")

        # build the streamlit resource with the code and the resources
        streamlit_resource = StreamlitResource()
        streamlit_resource.set_streamlit_code(code)
        streamlit_resource.set_env_shell_proxy(env_shell_proxy)
        streamlit_resource.set_params(params)
        streamlit_resource.add_multiple_resources(resources.to_list(), self.message_dispatcher)
        streamlit_resource.set_requires_authentication(requires_authentication)

        # install the env so it is not installed when viewing the app
        if env_shell_proxy is not None:
            env_shell_proxy.install_env()

        return streamlit_resource

    @classmethod
    def build_config_params_dict(cls, code: str, params: Dict[str, Any]) -> ConfigParamsDict:
        return {'code': code, "params": params}

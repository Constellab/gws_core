from gws_core.config.config_params import ConfigParams
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.code_param.yaml_code_param import YamlCodeParam
from gws_core.impl.agent.env_agent import EnvAgent
from gws_core.impl.agent.helper.agent_code_helper import AgentCodeHelper
from gws_core.impl.shell.pip_shell_proxy import PipShellProxy
from gws_core.model.typing_style import TypingIconType
from gws_core.streamlit.agents.streamlit_env_agent import StreamlitEnvAgent
from gws_core.streamlit.streamlit_resource import StreamlitResource
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs


@task_decorator(
    "StreamlitPipenvAgent",
    human_name="Streamlit pip env agent",
    short_description="Agent to generate a streamlit app dashboard in a pip environment",
    style=StreamlitResource.copy_style(
        icon_technical_name="agent", icon_type=TypingIconType.MATERIAL_ICON
    ),
)
class StreamlitPipenvAgent(StreamlitEnvAgent):
    config_specs = ConfigSpecs(
        {
            "params": EnvAgent.get_dynamic_param_config(),
            "env": YamlCodeParam(
                default_value=AgentCodeHelper.get_streamlit_pip_env_file_template(),
                human_name="Conda environment (YAML)",
                short_description="YAML configuration of the conda environment (contains the 'streamlit' package)",
            ),
            "code": AgentCodeHelper.get_streamlit_code_param(is_env=True),
            "requires_authentication": AgentCodeHelper.get_streamlit_requires_auth_param(),
        }
    )

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        shell_proxy = PipShellProxy.from_env_str(
            params.get_value("env"), message_dispatcher=self.message_dispatcher
        )
        streamlit_resource = self.run_agent(
            inputs.get("source"),
            params.get_value("params"),
            params.get_value("code"),
            params.get_value("requires_authentication"),
            params.get_value("env"),
            env_shell_proxy=shell_proxy,
        )

        return {"streamlit_app": streamlit_resource}

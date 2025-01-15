
from gws_core.config.config_params import ConfigParams
from gws_core.config.config_types import ConfigSpecs
from gws_core.config.param.code_param.python_code_param import PythonCodeParam
from gws_core.config.param.code_param.yaml_code_param import YamlCodeParam
from gws_core.impl.live.base.env_agent import EnvAgent
from gws_core.impl.live.helper.live_code_helper import LiveCodeHelper
from gws_core.impl.shell.base_env_shell import BaseEnvShell
from gws_core.impl.shell.conda_shell_proxy import CondaShellProxy
from gws_core.impl.shell.mamba_shell_proxy import MambaShellProxy
from gws_core.model.typing_style import TypingIconType
from gws_core.streamlit.agents.streamlit_env_agent import StreamlitEnvAgent
from gws_core.streamlit.streamlit_app import StreamlitAppType
from gws_core.streamlit.streamlit_resource import StreamlitResource
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs


@task_decorator("StreamlitCondaAgent", human_name="Streamlit conda agent",
                short_description="Agent to generate a streamlit app dashboard in a conda environment",
                style=StreamlitResource.copy_style(
                    icon_technical_name='agent', icon_type=TypingIconType.MATERIAL_ICON))
class StreamlitCondaAgent(StreamlitEnvAgent):

    config_specs: ConfigSpecs = {
        'params': EnvAgent.get_dynamic_param_config(),
        'env': YamlCodeParam(
            default_value=LiveCodeHelper.get_streamlit_conda_env_file_template(),
            human_name="Conda environment (YAML)", short_description="YAML configuration of the conda environment (contains the 'streamlit' package)"
        ),
        'code':
        PythonCodeParam(
            default_value=LiveCodeHelper.get_streamlit_env_code_template(),
            human_name="Streamlit app code",
            short_description="Code of the streamlit app to run")
    }

    def get_app_type(self) -> StreamlitAppType:
        return 'CONDA_ENV'

    def get_shell_proxy(self, env: str) -> BaseEnvShell:
        return CondaShellProxy.from_env_str(env, message_dispatcher=self.message_dispatcher)

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        shell_proxy = self.get_shell_proxy(params.get_value('env'))
        streamlit_resource = self.run_agent(inputs.get('source'),
                                            params.get_value('params'),
                                            self.get_app_type(),
                                            params.get_value('code'),
                                            params.get_value('env'),
                                            env_shell_proxy=shell_proxy)

        return {'streamlit_app': streamlit_resource}


@task_decorator("StreamlitMambaAgent", human_name="Streamlit mamba agent",
                short_description="Agent to generate a streamlit app dashboard in a mamba environment",
                style=StreamlitResource.copy_style(
                    icon_technical_name='agent', icon_type=TypingIconType.MATERIAL_ICON))
class StreamlitMambaAgent(StreamlitCondaAgent):

    def get_app_type(self) -> StreamlitAppType:
        return 'MAMBA_ENV'

    def get_shell_proxy(self, env: str) -> BaseEnvShell:
        return MambaShellProxy.from_env_str(env, message_dispatcher=self.message_dispatcher)

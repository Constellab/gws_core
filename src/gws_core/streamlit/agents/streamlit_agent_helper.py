
from gws_core.config.param.code_param.python_code_param import PythonCodeParam
from gws_core.config.param.param_spec import BoolParam
from gws_core.impl.agent.helper.agent_code_helper import AgentCodeHelper


class StreamlitAgentHelper():

    @classmethod
    def get_code_param(cls) -> PythonCodeParam:
        """Get the code parameter for the streamlit agent.
        """
        return PythonCodeParam(
            default_value=AgentCodeHelper.get_streamlit_code_template(),
            human_name="Streamlit app code",
            short_description="Code of the streamlit app to run"
        )

    @classmethod
    def get_requires_authentication_param(cls) -> BoolParam:
        """Get the requires authentication parameter for the streamlit agent.
        """
        return BoolParam(default_value=True,
                         visibility='protected',
                         human_name="Requires authentication",
                         short_description="If the app requires authentication"
                         )

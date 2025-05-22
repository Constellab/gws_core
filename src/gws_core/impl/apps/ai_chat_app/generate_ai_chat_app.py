from gws_core import (ConfigParams, ConfigSpecs, Dashboard, DashboardType,
                      InputSpecs, OutputSpec, OutputSpecs, StreamlitResource,
                      Task, TaskInputs, TaskOutputs, dashboard_decorator,
                      task_decorator)
from gws_core.credentials.credentials_param import CredentialsParam
from gws_core.credentials.credentials_type import CredentialsDataOther


@dashboard_decorator("AiChatAppDashboard", dashboard_type=DashboardType.STREAMLIT,
                     human_name="Generate show case app")
class AiChatAppDashboard(Dashboard):

    # retrieve the path of the app folder, relative to this file
    # the dashboard code folder starts with a underscore to avoid being loaded when the brick is loaded
    def get_app_folder_path(self):
        return self.get_app_folder_from_relative_path(__file__, "_ai_chat_app")


@task_decorator("GenerateAiChatApp", human_name="Generate AiChatApp app",
                style=StreamlitResource.copy_style())
class GenerateAiChatApp(Task):
    """
    Task that generates the AiChatApp app.
    """

    input_specs = InputSpecs()
    output_specs = OutputSpecs({
        'streamlit_app': OutputSpec(StreamlitResource)
    })

    config_specs = ConfigSpecs({
        'chat_credentials': CredentialsParam(
            human_name="Chat credentials",
            short_description="Credentials to access a specific dify chat",
        ),
    })

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        """ Run the task """

        chat_credentials_data: CredentialsDataOther = params['chat_credentials']

        streamlit_app = StreamlitResource()
        streamlit_app.set_param('chat_credentials_name', chat_credentials_data.meta.name)


        streamlit_app.set_dashboard(AiChatAppDashboard())
        streamlit_app.name = "AiChatApp"
        streamlit_app.set_requires_authentication(False)

        return {"streamlit_app": streamlit_app}

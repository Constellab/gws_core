from gws_core import (ConfigParams, ConfigSpecs, Dashboard, DashboardType,
                      InputSpecs, OutputSpec, OutputSpecs, StreamlitResource,
                      Task, TaskInputs, TaskOutputs, dashboard_decorator,
                      task_decorator)
from gws_core.config.param.param_spec import BoolParam, StrParam
from gws_core.credentials.credentials_param import CredentialsParam
from gws_core.credentials.credentials_type import CredentialsDataOther


@dashboard_decorator("DatahubDifyAppDashboard", dashboard_type=DashboardType.STREAMLIT,
                     human_name="Generate show case app")
class DatahubDifyAppDashboard(Dashboard):

    # retrieve the path of the app folder, relative to this file
    # the dashboard code folder starts with a underscore to avoid being loaded when the brick is loaded
    def get_app_folder_path(self):
        return self.get_app_folder_from_relative_path(__file__, "_datahub_dify_app")


@task_decorator("GenerateDatahubDifyApp", human_name="Generate DatahubDifyApp app",
                style=StreamlitResource.copy_style())
class GenerateDatahubDifyApp(Task):
    """
    Task that generates the DatahubDifyApp app.
    """

    input_specs = InputSpecs()
    output_specs = OutputSpecs({
        'streamlit_app': OutputSpec(StreamlitResource)
    })

    config_specs = ConfigSpecs({
        'chat_credentials': CredentialsParam(
            human_name="Chat credentials",
            short_description="Credentials to access the dify chat",
        ),
        'knowledge_base_credentials': CredentialsParam(
            human_name="Knowledge Base credentials",
            short_description="Credentials to access all knowledge bases",
        ),
        'knowledge_base_id': StrParam(
            human_name="Knowledge Base ID",
            short_description="ID of the knowledge base to use",
        ),
        'show_config_page': BoolParam(
            human_name="Show config page",
            short_description="Show the config page",
            default_value=True
        ),
    })

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        """ Run the task """

        streamlit_app = StreamlitResource()

        chat_credentials_data: CredentialsDataOther = params['chat_credentials']
        streamlit_app.set_param('chat_credentials_name', chat_credentials_data.meta.name)

        knowledge_base_credentials_data: CredentialsDataOther = params['knowledge_base_credentials']
        streamlit_app.set_param('knowledge_base_credentials_name', knowledge_base_credentials_data.meta.name)

        streamlit_app.set_param('knowledge_base_id', params['knowledge_base_id'])
        streamlit_app.set_param('show_config_page', params['show_config_page'])

        streamlit_app.set_dashboard(DatahubDifyAppDashboard())
        streamlit_app.name = "Datahub dify app"

        return {"streamlit_app": streamlit_app}

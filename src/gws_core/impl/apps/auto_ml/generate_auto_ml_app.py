
import os

from gws_core.config.config_params import ConfigParams
from gws_core.io.io_spec import OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.streamlit.streamlit_dashboard import (Dashboard, DashboardType,
                                                    dashboard_decorator)
from gws_core.streamlit.streamlit_resource import StreamlitResource
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs


@dashboard_decorator("GenerateAutoMLAppDashboard", dashboard_type=DashboardType.STREAMLIT,
                     human_name="Generate auto machine learning app")
class GenerateAutoMLAppDashboard(Dashboard):

    # retrieve the path of the app folder, relative to this file
    # the dashboard code folder starts with a underscore to avoid being loaded when the brick is loaded
    def get_app_folder_path(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            "_test_streamlit_dashboard"
        )

    # def get_shell_proxy(self) -> ShellProxy:
    #     env_path = os.path.join(
    #         self.get_app_folder_path(),
    #         'streamlit_env.yml',
    #     )
    #     return MambaShellProxy(env_path)


@task_decorator("GenerateAutoMLApp", human_name="Generate auto machine learning app")
class GenerateAutoMLApp(Task):
    """
    Task description (supports markdown)
    """

    input_specs = InputSpecs()
    output_specs = OutputSpecs({
        'streamlit_app': OutputSpec(StreamlitResource)
    })

    config_specs = {}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        """ Run the task """

        streamlit_app = StreamlitResource()

        streamlit_app.set_dashboard(GenerateAutoMLAppDashboard())

        return {"streamlit_app": streamlit_app}

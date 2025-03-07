
import os

from gws_core.config.config_params import ConfigParams
from gws_core.io.io_spec import OutputSpec
from gws_core.io.io_specs import OutputSpecs
from gws_core.streamlit.streamlit_dashboard import (Dashboard, DashboardType,
                                                    dashboard_decorator)
from gws_core.streamlit.streamlit_resource import StreamlitResource
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs


@dashboard_decorator("ShowcaseApp", dashboard_type=DashboardType.STREAMLIT,
                     human_name="Generate show case app")
class ShowcaseApp(Dashboard):

    # retrieve the path of the app folder, relative to this file
    # the dashboard code folder starts with a underscore to avoid being loaded when the brick is loaded
    def get_app_folder_path(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            "_showcase_app"
        )


@task_decorator("GenerateShowcaseApp", human_name="Generate streamlit showcase app",
                short_description="App that showacases Constellab components for streamlit",
                style=StreamlitResource.copy_style())
class GenerateShowcaseApp(Task):
    """
    Task description (supports markdown)
    """

    output_specs = OutputSpecs({
        'streamlit_app': OutputSpec(StreamlitResource)
    })

    config_specs = {}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        """ Run the task """

        streamlit_app = StreamlitResource()

        streamlit_app.set_dashboard(ShowcaseApp())

        return {"streamlit_app": streamlit_app}

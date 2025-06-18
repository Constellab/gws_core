
from gws_core.apps.app_config import AppConfig, app_decorator
from gws_core.apps.app_dto import AppType
from gws_core.config.config_params import ConfigParams
from gws_core.config.config_specs import ConfigSpecs
from gws_core.io.io_spec import OutputSpec
from gws_core.io.io_specs import OutputSpecs
from gws_core.streamlit.streamlit_resource import StreamlitResource
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs


@app_decorator("ShowcaseApp", app_type=AppType.STREAMLIT,
               human_name="Generate show case app")
class ShowcaseApp(AppConfig):

    # retrieve the path of the app folder, relative to this file
    # the dashboard code folder starts with a underscore to avoid being loaded when the brick is loaded
    def get_app_folder_path(self):
        return self.get_app_folder_from_relative_path(
            __file__,
            "_showcase_app"
        )


@task_decorator("GenerateShowcaseApp", human_name="Generate streamlit showcase app",
                short_description="App that showcases Constellab components for streamlit",
                style=StreamlitResource.copy_style())
class GenerateShowcaseApp(Task):
    """
    Task that generates the streamlit showcase app.

    This app showcases the streamlit component developped by Gencovery to simplify
    the creation of streamlit apps.

    Some components are generic streamlit components (like containers), other wrap Constellab UI components.
    """

    output_specs = OutputSpecs({
        'streamlit_app': OutputSpec(StreamlitResource)
    })

    config_specs = ConfigSpecs({})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        """ Run the task """

        streamlit_app = StreamlitResource()

        streamlit_app.set_app_config(ShowcaseApp())
        streamlit_app.set_requires_authentication(False)
        streamlit_app.set_name("Streamlit showcase App")

        return {"streamlit_app": streamlit_app}

import os

from gws_core.apps.app_config import AppConfig, app_decorator
from gws_core.apps.app_dto import AppType
from gws_core.apps.streamlit.streamlit_resource import StreamlitResource
from gws_core.config.config_params import ConfigParams
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import BoolParam, StrParam
from gws_core.io.io_spec import OutputSpec
from gws_core.io.io_specs import OutputSpecs
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs


@app_decorator(
    "StreamlitShowcaseApp", app_type=AppType.STREAMLIT, human_name="Generate streamlit showcase app"
)
class StreamlitShowcaseApp(AppConfig):
    # retrieve the path of the app folder, relative to this file
    # the dashboard code folder starts with a underscore to avoid being loaded when the brick is loaded
    def get_app_folder_path(self):
        return self.get_app_folder_from_relative_path(__file__, "_streamlit_showcase_app")

    def get_dev_config_json_path(self) -> str:
        """Get the path to the dev config json file.

        :return: path to the dev config json file
        :rtype: str
        """
        return os.path.join(self.get_app_folder_path(), "dev_config.json")


@task_decorator(
    "GenerateStreamlitShowcaseApp",
    human_name="Generate streamlit showcase app",
    short_description="App that showcases Constellab components for streamlit",
    style=StreamlitResource.copy_style(),
)
class GenerateStreamlitShowcaseApp(Task):
    """
    Task that generates the streamlit showcase app.

    This app showcases the streamlit component developped by Gencovery to simplify
    the creation of streamlit apps.

    Some components are generic streamlit components (like containers), other wrap Constellab UI components.
    """

    output_specs = OutputSpecs({"streamlit_app": OutputSpec(StreamlitResource)})

    config_specs = ConfigSpecs(
        {
            "custom_subdomain": StrParam(
                default_value="",
                optional=True,
                human_name="Custom subdomain",
                short_description="Optional readable, stable subdomain for the app "
                "(e.g. 'app-hello-world'). Leave empty to use the default id-based host.",
            ),
            "requires_authentication": BoolParam(
                default_value=False,
                human_name="Requires authentication",
                short_description="Whether the app requires the user to be authenticated to access it.",
            ),
        }
    )

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        """Run the task"""

        streamlit_app = StreamlitResource()

        streamlit_app.set_app_config(StreamlitShowcaseApp())
        streamlit_app.set_requires_authentication(params.get_value("requires_authentication"))
        streamlit_app.set_name("Streamlit showcase App")

        custom_subdomain = params.get_value("custom_subdomain")
        if custom_subdomain:
            streamlit_app.set_custom_subdomain(custom_subdomain)

        return {"streamlit_app": streamlit_app}

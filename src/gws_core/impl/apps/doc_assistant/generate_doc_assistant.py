from gws_core.apps.app_config import AppConfig, app_decorator
from gws_core.apps.app_dto import AppType
from gws_core.apps.streamlit.streamlit_resource import StreamlitResource
from gws_core.config.config_params import ConfigParams
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import TextParam
from gws_core.io.io_spec import OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs


@app_decorator("GenerateDocAssistant", app_type=AppType.STREAMLIT)
class GenerateDocAssistantDashboard(AppConfig):
    # retrieve the path of the app folder, relative to this file
    # the dashboard code folder starts with a underscore to avoid being loaded when the brick is loaded
    def get_app_folder_path(self):
        return self.get_app_folder_from_relative_path(__file__, "_doc_assistant_app")


@task_decorator(
    "GenerateDocAssistant",
    human_name="Generate documentation AI assistant",
    short_description="Task to generate the documentation AI assistant app",
)
class GenerateDocAssistant(Task):
    """
    Task that generates the documentation AI assistant app.

    Execute this task to have access to the documentation AI assistant app.

    This app helps you to generate documentation :
    - for your product
    - for you tasks
    """

    input_specs = InputSpecs()

    output_specs = OutputSpecs({"streamlit_app": OutputSpec(StreamlitResource)})

    config_specs = ConfigSpecs(
        {
            "prompts_json_path": TextParam(
                human_name="Prompts JSON file path",
                short_description="Path to the JSON file containing all prompts",
            ),
        }
    )

    def run(self, params: ConfigParams, _inputs: TaskInputs) -> TaskOutputs:
        """Run the task"""

        streamlit_app = StreamlitResource()

        streamlit_app.set_app_config(GenerateDocAssistantDashboard())
        streamlit_app.name = "Documentation AI assistant"
        streamlit_app.set_requires_authentication(False)

        streamlit_app.set_param("prompts_json_path", params["prompts_json_path"])

        return {"streamlit_app": streamlit_app}

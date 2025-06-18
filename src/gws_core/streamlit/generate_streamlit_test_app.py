
from gws_core.apps.app_config import AppConfig, AppType, app_decorator
from gws_core.config.config_params import ConfigParams
from gws_core.config.config_specs import ConfigSpecs
from gws_core.impl.file.folder import Folder
from gws_core.io.io_spec import OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.streamlit.streamlit_resource import StreamlitResource
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs


@app_decorator("GenerateStreamlitTestApp", app_type=AppType.STREAMLIT,
               human_name="Test dashboard for gws_core")
class TestDashboard(AppConfig):

    # retrieve the path of the app folder, relative to this file
    # the dashboard code folder starts with a underscore to avoid being loaded when the brick is loaded
    def get_app_folder_path(self):
        return self.get_app_folder_from_relative_path(
            __file__,
            "_test_streamlit_dashboard"
        )

    # def get_shell_proxy(self) -> ShellProxy:
    #     env_path = os.path.join(
    #         self.get_app_folder_path(),
    #         'streamlit_env.yml',
    #     )
    #     return MambaShellProxy(env_path)


@task_decorator("GenerateStreamlitTestApp", human_name="GenerateStreamlitTestApp", hide=True)
class GenerateStreamlitTestApp(Task):
    """
    Task description (supports markdown)
    """

    input_specs = InputSpecs()
    output_specs = OutputSpecs({
        'streamlit_app': OutputSpec(StreamlitResource)
    })

    config_specs = ConfigSpecs({})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        """ Run the task """

        streamlit_app = StreamlitResource()

        tmp_dir = self.create_tmp_dir()
        streamlit_app.add_resource(Folder(tmp_dir))

        streamlit_app.set_app_config(TestDashboard())

        return {"streamlit_app": streamlit_app}

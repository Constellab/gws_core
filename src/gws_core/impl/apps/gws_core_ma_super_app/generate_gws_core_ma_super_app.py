from gws_core import (ConfigParams, AppConfig, AppType, OutputSpec,
                      OutputSpecs, StreamlitResource, Task, TaskInputs,
                      TaskOutputs, app_decorator, task_decorator, 
                      InputSpecs, ConfigSpecs)


@app_decorator("GwsCoreMaSuperAppAppConfig", app_type=AppType.STREAMLIT,
               human_name="Generate GwsCoreMaSuperApp app")
class GwsCoreMaSuperAppAppConfig(AppConfig):

    # retrieve the path of the app folder, relative to this file
    # the app code folder starts with a underscore to avoid being loaded when the brick is loaded
    def get_app_folder_path(self):
        return self.get_app_folder_from_relative_path(__file__, "_gws_core_ma_super_app")


@task_decorator("GenerateGwsCoreMaSuperApp", human_name="Generate GwsCoreMaSuperApp app",
                style=StreamlitResource.copy_style())
class GenerateGwsCoreMaSuperApp(Task):
    """
    Task that generates the GwsCoreMaSuperApp app.
    """

    input_specs = InputSpecs()
    output_specs = OutputSpecs({
        'streamlit_app': OutputSpec(StreamlitResource)
    })

    config_specs = ConfigSpecs({})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        """ Run the task """

        streamlit_app = StreamlitResource()

        streamlit_app.set_app_config(GwsCoreMaSuperAppAppConfig())
        streamlit_app.name = "GwsCoreMaSuperApp"

        return {"streamlit_app": streamlit_app}

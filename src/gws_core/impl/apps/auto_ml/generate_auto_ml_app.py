
from gws_core.config.config_params import ConfigParams
from gws_core.impl.table.table import Table
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.note.task.lab_note_resource import LabNoteResource
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
        return self.get_app_folder_from_relative_path(
            __file__,
            "_auto_ml_app"
        )


@task_decorator("GenerateAutoMLApp", human_name="Generate ML Copilot App",
                short_description="Task to generate the copilot machine learning app",
                style=StreamlitResource.copy_style())
class GenerateAutoMLApp(Task):
    """
    Task that generates the copilot machine learning app.

    Execute this task to have access to the copilot machine learning app.

    You can provide a note to be displayed in the getting started section of the app.

    You can provide a table to initialize the dashboard with data.
    """

    input_specs = InputSpecs({
        'getting_started_note': InputSpec(LabNoteResource, human_name='Getting started note',
                                          short_description='Note that is being displayed in the getting started section'),
        'table': InputSpec(Table, human_name='Table', short_description='Optional table to init dashboard with', is_optional=True)
    })
    output_specs = OutputSpecs({
        'streamlit_app': OutputSpec(StreamlitResource)
    })

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        """ Run the task """

        streamlit_app = StreamlitResource()

        streamlit_app.set_dashboard(GenerateAutoMLAppDashboard())
        streamlit_app.name = 'Machine Learning Copilot'
        streamlit_app.add_resource(inputs['getting_started_note'], create_new_resource=False)
        streamlit_app.set_requires_authentication(False)

        table = inputs.get('table')
        if table is not None:
            streamlit_app.add_resource(table, create_new_resource=False)

        return {"streamlit_app": streamlit_app}

# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
import plotly.graph_objs as go

from gws_core.config.config_types import ConfigParams
from gws_core.impl.json.json_dict import JSONDict
from gws_core.impl.openai.open_ai_helper import OpenAiHelper
from gws_core.impl.openai.smart_task_base import SmartTaskBase
from gws_core.impl.table.table import Table
from gws_core.impl.text.text import Text
from gws_core.impl.view.plotly_view import PlotlyView
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_spec_helper import InputSpecs, OutputSpecs
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs


@task_decorator("SmartPlotly", human_name="Smart plotly generator",
                short_description="Generate a plot using an AI (OpenAI).")
class SmartPlotly(SmartTaskBase):
    """
This task is still in beta version.

This task uses openAI API to generate python code that generate a chart using matplotlib library. This code is then automaticaaly executed.

/!\ This task does not support table tags.

The data of the table is not transferered to OpenAI, only the provided text.
    """

    input_specs: InputSpecs = {
        'source': InputSpec(Table),
    }
    output_specs: OutputSpecs = {
        'target': OutputSpec(JSONDict, human_name='Plot', short_description='Generated plot file by the AI.'),
        'generated_code': SmartTaskBase.generated_code_output
    }

    def get_context(self, params: ConfigParams, inputs: TaskInputs) -> str:
        # prepare the input
        table: Table = inputs["source"]

        context = "Your are a developer assistant that generate code in python to generate plotly express figure from dataframe."
        context += "The variable named 'source' contains the dataframe."
        context += "The generated plotly express figure must be assigned to variable named 'target'."
        context += "Only build the figure object, do not display the figure using 'show' method."
        context += f"{OpenAiHelper.generate_code_rules}"
        context += f"The dataframe has {table.nb_rows} rows and {table.nb_columns} columns."

        return context

    def build_openai_code_inputs(self, params: ConfigParams, inputs: TaskInputs) -> dict:
        # prepare the input
        table: Table = inputs["source"]

        return {"source": table.get_data()}

    def build_task_outputs(self, params: ConfigParams, inputs: TaskInputs,
                           code_outputs: dict, generated_code: str) -> dict:
        target = code_outputs.get("target", None)

        if target is None:
            raise Exception("The code did not generate any output")

        if not isinstance(target, go.Figure):
            raise Exception("The output must be a plotly figure")

        # convert the plotly figure to a json dict
        view = PlotlyView(target)
        json_dict = JSONDict(view.to_dict(ConfigParams()))

        # make the output code compatible with the live task
        live_task_code = f"""
from gws_core import File, PlotlyView, JSONDict
import os
source = source.get_data()
{generated_code}
view = PlotlyView(target)
target = JSONDict(view.to_dict(ConfigParams()))"""

        return {'target': json_dict, 'generated_code': Text(live_task_code)}

# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
import plotly.graph_objs as go

from gws_core.config.config_params import ConfigParams
from gws_core.core.utils.gws_core_packages import GwsCorePackages
from gws_core.impl.openai.open_ai_helper import OpenAiHelper
from gws_core.impl.openai.smart_task_base import SmartTaskBase
from gws_core.impl.table.table import Table
from gws_core.impl.text.text import Text
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs

from .plotly_resource import PlotlyResource


@task_decorator("SmartPlotly", human_name="Smart interactive plot generator",
                short_description="Generate an interactive plot using an AI (OpenAI).")
class SmartPlotly(SmartTaskBase):
    """
This task is still in beta version.

This task uses openAI API to generate python code that generate an interactive chart using plotly library. This code is then automatically executed.

/!\ This task does not support table tags.

The data of the table is not transferered to OpenAI, only the provided text.
    """

    input_specs: InputSpecs = InputSpecs({
        'source': InputSpec(Table),
    })
    output_specs: OutputSpecs = OutputSpecs({
        'target': OutputSpec(PlotlyResource, human_name='Plot', short_description='Generated plot file by the AI.'),
        'generated_code': SmartTaskBase.generated_code_output
    })

    def get_context(self, params: ConfigParams, inputs: TaskInputs) -> str:
        # prepare the input
        table: Table = inputs["source"]

        context = "You are a developer assistant that generate code in python to generate plotly express figure from dataframe."
        context += "\nThe variable named 'source' contains the dataframe."
        context += "The generated plotly express figure must be assigned to variable named 'target'."
        context += " Only build the figure object, do not display the figure using 'show' method."
        context += f"\n{OpenAiHelper.get_code_context([GwsCorePackages.PANDAS, GwsCorePackages.NUMPY, GwsCorePackages.PLOTLY])}"
        context += f"\nThe dataframe has {table.nb_rows} rows and {table.nb_columns} columns."

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
        plotly_resource = PlotlyResource(target)

        # make the output code compatible with the live task
        live_task_code = f"""
from gws_core import File, PlotlyResource
import os
# get DataFrame from the source
source = source[0].get_data()
{generated_code}
# save the figure as resource
target = [PlotlyResource(target)]"""

        generated_text = Text(live_task_code)
        generated_text.name = "Interactive plot code"

        return {'target': plotly_resource, 'generated_code': generated_text}


from typing import Any, Dict, List

import plotly.graph_objs as go

from gws_core.config.config_params import ConfigParams
from gws_core.config.config_specs import ConfigSpecs
from gws_core.core.utils.gws_core_packages import GwsCorePackages
from gws_core.impl.openai.ai_prompt_code import (AIPromptCode,
                                                 AIPromptCodeContext)
from gws_core.impl.openai.open_ai_chat import OpenAiChat
from gws_core.impl.openai.open_ai_chat_param import OpenAiChatParam
from gws_core.impl.table.table import Table
from gws_core.impl.text.text import Text
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.model.typing_style import TypingStyle
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs

from ...plotly.plotly_resource import PlotlyResource


class AITableGeneratePlotly(AIPromptCode):
    """Class to call AI to generate a plotly figure from a table.
    The data of the table is not transferered to OpenAI, only the provided text.
    """

    table: Table

    def __init__(self, table: Table, chat: OpenAiChat, message_dispatcher=None):
        super().__init__(chat, message_dispatcher)
        self.table = table

    def build_main_context(self, context: AIPromptCodeContext) -> str:
        # prepare the input
        return f"""{context.python_code_intro}
The code purpose is to generate a plotly express figure from a DataFrame.
{context.inputs_description}
The dataframe has {self.table.nb_rows} rows and {self.table.nb_columns} columns.
{context.outputs_description}
Only build the figure object, do not display the figure using 'show' method.
{context.code_rules}"""

    def build_code_inputs(self) -> dict:
        # prepare the input
        return {"source": self.table.get_data()}

    def get_code_expected_output_types(self) -> Dict[str, Any]:
        return {"target": go.Figure}

    def get_available_package_names(self) -> List[str]:
        return [GwsCorePackages.PANDAS, GwsCorePackages.NUMPY, GwsCorePackages.PLOTLY]

    def build_output(self, code_outputs: dict) -> PlotlyResource:
        target = code_outputs.get("target", None)

        if target is None:
            raise Exception("The code did not generate any output")

        if not isinstance(target, go.Figure):
            raise Exception("The output must be a plotly figure")

        # convert the plotly figure to a json dict
        return PlotlyResource(target)

    def _generate_agent_code(self, generated_code: str) -> str:
        return f"""
from gws_core import File, PlotlyResource
import os
# get DataFrame from the source
source = sources[0].get_data()
{generated_code}
# save the figure as resource
targets = [PlotlyResource(target)]"""


@task_decorator("SmartPlotly", human_name="Smart interactive plot generator",
                short_description="Generate an interactive plot using an AI (OpenAI).",
                style=TypingStyle.material_icon("insights"))
class SmartPlotly(Task):
    """
    This tasks uses AI to generate an interactive plot using Plotly from a table.

    The data of the table is not transferered to OpenAI, only the provided text.
    Please provide a clear description of what you want to achieve by providing column names, row names, etc.
    You can provide multiple message to the AI to get the best result, the context will be kept between the messages.

    This task uses openAI API to generate python code which is then automatically executed.

    ⚠️ This task does not support table tags. ⚠️
    """

    input_specs: InputSpecs = InputSpecs({
        'source': InputSpec(Table),
    })
    output_specs: OutputSpecs = OutputSpecs({
        'target': OutputSpec(PlotlyResource, human_name='Plot', short_description='Generated plot file by the AI.'),
        'generated_code': AITableGeneratePlotly.generate_agent_code_task_output_config()
    })

    config_specs = ConfigSpecs({
        'prompt': OpenAiChatParam()
    })

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        chat: OpenAiChat = params.get_value('prompt')

        smart_plotly = AITableGeneratePlotly(inputs["source"], chat, self.message_dispatcher)
        plotly_resource: PlotlyResource = smart_plotly.run()

        # save the new config with the new prompt
        params.set_value('prompt', smart_plotly.chat)
        params.save_params()

        generated_text = Text(smart_plotly.generate_agent_code())
        generated_text.name = "Interactive plot code"

        return {'target': plotly_resource, 'generated_code': generated_text}

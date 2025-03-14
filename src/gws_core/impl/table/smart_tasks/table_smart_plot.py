

from typing import Any, Dict, List

from gws_core.config.config_params import ConfigParams
from gws_core.config.config_types import ConfigSpecs
from gws_core.core.utils.gws_core_packages import GwsCorePackages
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file import File
from gws_core.impl.file.file_helper import FileHelper
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


class AITableGeneratePlotImage(AIPromptCode):
    """
    Class to call AI to generate a plot image from a table.
    The data of the table is not transferered to OpenAI, only the provided text.
    """

    table: Table

    def __init__(self, table: Table, chat: OpenAiChat, message_dispatcher=None):
        super().__init__(chat, message_dispatcher)
        self.table = table

    def build_main_context(self, context: AIPromptCodeContext) -> str:

        return f"""{context.python_code_intro}
The code purpose is to modify generate a plot file from a DataFrame using matplotlib.
{context.inputs_description}
The dataframe has {self.table.nb_rows} rows and {self.table.nb_columns} columns.
The variable named 'output_path' contains the absolute path of the output png file destination. Don't use the show method.
{context.code_rules}"""

    def get_code_expected_output_types(self) -> Dict[str, Any]:
        return {}

    def get_available_package_names(self) -> List[str]:
        return [GwsCorePackages.PANDAS, GwsCorePackages.NUMPY, GwsCorePackages.MATPLOTLIB]

    def build_code_inputs(self) -> dict:
        # execute the live code
        temp_dir = Settings.make_temp_dir()
        output_path = temp_dir + "/output.png"

        # all variable accessible in the generated code
        return {"source": self.table.get_data(), 'output_path': output_path}

    def build_output(self, code_outputs: dict) -> File:
        output_path = code_outputs.get("output_path", None)

        if output_path is None:
            raise Exception("The code did not generate any file")

        if not FileHelper.exists_on_os(output_path) or not FileHelper.is_file(output_path):
            raise Exception("The output must be a file")

        return File(output_path)

    def _generate_agent_code(self, generated_code):
        return f"""
from gws_core import File
import os
source = sources[0].get_data()
# generate the output file path
output_path = os.path.join(working_dir, 'output.png')
{generated_code}
targets = [File(output_path)]"""


@task_decorator("SmartPlot", human_name="Smart plot generator",
                short_description="Generate a plot using an AI (OpenAI).",
                style=TypingStyle.material_icon("auto_awesome"))
class SmartPlot(Task):
    """
    This task uses AI to generate a plot image from a table. It uses the matplotlib library.

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
        'target': OutputSpec(File, human_name='Plot', short_description='Generated plot file by the AI.'),
        'generated_code': AITableGeneratePlotImage.generate_agent_code_task_output_config()
    })

    config_specs: ConfigSpecs = {
        'prompt': OpenAiChatParam()
    }

    temp_dir: str
    ouput_path: str

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        chat: OpenAiChat = params.get_value('prompt')

        smart_plotly = AITableGeneratePlotImage(inputs["source"], chat, self.message_dispatcher)
        file: File = smart_plotly.run()

        # save the new config with the new prompt
        params.set_value('prompt', smart_plotly.chat)
        params.save_params()

        generated_text = Text(smart_plotly.generate_agent_code())
        generated_text.name = "Plot code"

        return {'target': file, 'generated_code': generated_text}



from typing import Any, Dict, List, Type

from pandas import DataFrame

from gws_core.config.config_params import ConfigParams
from gws_core.config.config_types import ConfigSpecs
from gws_core.core.utils.gws_core_packages import GwsCorePackages
from gws_core.impl.openai.ai_prompt_code import (AIPromptCode,
                                                 AIPromptCodeContext)
from gws_core.impl.openai.open_ai_chat import OpenAiChat
from gws_core.impl.openai.open_ai_chat_param import OpenAiChatParam
from gws_core.impl.openai.open_ai_helper import OpenAiHelper
from gws_core.impl.table.table import Table
from gws_core.io.dynamic_io import DynamicInputs, DynamicOutputs
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.resource_set.resource_list import ResourceList
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs


class AIMultiTableTransformer(AIPromptCode):
    """
    Class to call AI to generate a python code that transforms multiple tables.
    The data of the table is not transferered to OpenAI, only the provided text.
    """

    tables: List[Table]

    def __init__(self, tables: List[Table], chat: OpenAiChat, message_dispatcher=None):
        super().__init__(chat, message_dispatcher)
        self.tables = tables

    def build_main_context(self, context: AIPromptCodeContext) -> str:
        return f"""{context.python_code_intro}
The code purpose is to modify multiple dataframes.
{context.inputs_description}
There are {len(self.tables)} dataframes in the list.
{context.outputs_description}
{context.code_rules}"""

    def build_code_inputs(self) -> dict:
        # get the table
        dataframes: List[DataFrame] = []
        i = 0
        for resource in self.tables:
            if isinstance(resource, Table):
                dataframes.append(resource.get_data())
            else:
                raise Exception(f"Resource n°{i} is not a DataFrame")
            i += 1

        # pass the dataframe as input
        return {"source": dataframes}

    def build_inputs_context(self, code_inputs: Dict[str, Any]) -> str:
        return OpenAiHelper.describe_inputs_text_for_context("'source' (type 'List[DataFrame]')")

    def build_outputs_context(self) -> str:
        return OpenAiHelper.describe_outputs_text_for_context("'target' (type 'List[DataFrame]')")

    def get_code_expected_output_types(self) -> Dict[str, Type]:
        pass

    def get_available_package_names(self) -> List[str]:
        return [GwsCorePackages.PANDAS, GwsCorePackages.NUMPY, GwsCorePackages.PLOTLY]

    def build_output(self, code_outputs: dict) -> List[Table]:
        output: List[DataFrame] = code_outputs.get("target", None)

        if output is None:
            raise Exception("The code did not generate any output")

        if not isinstance(output, list):
            raise Exception("The output must be a list of pandas DataFrame")

        results: List[Table] = []

        for dataframe in output:
            results.append(Table(dataframe))

        return results

    def _generate_agent_code(self, generated_code: str) -> str:
        return f"""from gws_core import Table
# keep the original table
# retrieve the dataframe for the generated code
source = [s.get_data() for s in sources]
{generated_code}
# convert the dataframe to a table
targets = [Table(t) for t in target]"""


@task_decorator("MultiTableSmartTransformer", human_name="Smart multi tables transformer",
                short_description="Multi tables transformer that uses AI (OpenAI).",
                style=TypingStyle.material_icon("auto_awesome"))
class MultiTableSmartTransformer(Task):
    """
    This tasks uses AI to transform multiple tables. It supports multiple tables as input and output.

    This task can be useful to merge multiple tables, filter them, compare them, etc.

    The data of the table is not transferered to OpenAI, only the provided text.
    Please provide a clear description of what you want to achieve by providing column names, row names, etc.
    You can provide multiple message to the AI to get the best result, the context will be kept between the messages.

    This task uses openAI API to generate python code which is then automatically executed.

    ⚠️ This task does not support table tags. ⚠️
    """

    input_specs: InputSpecs = DynamicInputs({
        'source': InputSpec(Table),
    }, additionnal_port_spec=InputSpec(Table))

    output_specs: OutputSpecs = DynamicOutputs({
        'target': OutputSpec(Table),
    }, additionnal_port_spec=OutputSpec(Table))

    config_specs: ConfigSpecs = {
        'prompt': OpenAiChatParam()
    }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        chat: OpenAiChat = params.get_value('prompt')

        ai_tables = AIMultiTableTransformer(inputs["source"], chat, self.message_dispatcher)
        result: List[Table] = ai_tables.run()

        # save the new config with the new prompt
        params.set_value('prompt', ai_tables.chat)
        params.save_params()

        # only log the code that is generated
        self.log_info_message(f"""##################### AGENT CODE #####################
{ai_tables.generate_agent_code()}
##################### AGENT CODE ###################""")

        return {'target': ResourceList(result)}

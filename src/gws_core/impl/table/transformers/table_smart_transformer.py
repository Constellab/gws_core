

from typing import Any, Dict, List

from pandas import DataFrame

from gws_core.config.config_params import ConfigParams
from gws_core.config.config_types import ConfigSpecs
from gws_core.config.param.param_spec import BoolParam
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


class AITableTransformer(AIPromptCode):
    """
    Class to call AI to generate a python code that transforms a table.
    The data of the table is not transferered to OpenAI, only the provided text.
    """

    table: Table
    keep_columns_tags: bool
    keep_rows_tags: bool

    def __init__(self, table: Table, chat: OpenAiChat,
                 keep_columns_tags: bool = False, keep_rows_tags: bool = False,
                 message_dispatcher=None):
        super().__init__(chat, message_dispatcher)
        self.table = table
        self.keep_columns_tags = keep_columns_tags
        self.keep_rows_tags = keep_rows_tags

    def build_main_context(self, context: AIPromptCodeContext) -> str:
        # prepare the input

        return f"""{context.python_code_intro}
The code purpose is to modify a dataframe.
{context.inputs_description}
The dataframe has {self.table.nb_rows} rows and {self.table.nb_columns} columns.
{context.outputs_description}
{context.code_rules}"""

    def build_code_inputs(self) -> dict:
        # pass the dataframe as input
        return {"source": self.table.get_data()}

    def get_code_expected_output_types(self) -> Dict[str, Any]:
        return {"target": DataFrame}

    def get_available_package_names(self) -> List[str]:
        return [GwsCorePackages.PANDAS, GwsCorePackages.NUMPY, GwsCorePackages.PLOTLY]

    def build_output(self, code_outputs: dict) -> Table:
        output = code_outputs.get("target", None)

        if output is None:
            raise Exception("The code did not generate any output")

        if not isinstance(output, DataFrame):
            raise Exception("The output must be a pandas DataFrame")

        result = Table(output)

        # manager the tags options
        if self.keep_columns_tags:
            # copy the tags from the source table to the target table
            result.copy_column_tags_by_name(self.table)

        if self.keep_rows_tags:
            result.copy_row_tags_by_name(self.table)

        return result

    def _generate_agent_code(self, generated_code: str) -> str:
        # make the output code compatible with the agent
        agent_code = f"""
from gws_core import Table
# keep the original table
source_table = sources[0]
# retrieve the dataframe for the generated code
source = sources[0].get_data()
{generated_code}
# convert the dataframe to a table
table_target = Table(target)
"""
        # manager the tags options
        if self.keep_columns_tags:
            # update the agent code to copy the tags
            agent_code += "\ntable_target.copy_column_tags_by_name(source_table)"

        if self.keep_rows_tags:
            agent_code += "\ntable_target.copy_row_tags_by_name(source_table)"

        # set an the output as array
        agent_code += "\ntargets = [table_target]"

        return agent_code


@task_decorator("SmartTableTransformer", human_name="Smart table transformer",
                short_description="Table transformer that uses AI  (OpenAI).",
                style=TypingStyle.material_icon("auto_awesome"))
class TableSmartTransformer(Task):
    """
    This task uses openAI API to generate python code that transforms a dataframe. This code is then automatically executed.

    The data of the table is not transferered to OpenAI, only the provided text.
    """

    input_specs: InputSpecs = InputSpecs({
        'source': InputSpec(Table),
    })
    output_specs: OutputSpecs = OutputSpecs({
        'target': OutputSpec(Table),
        'generated_code': AITableTransformer.generate_agent_code_task_output_config()
    })
    config_specs: ConfigSpecs = {
        # get the openAI config specs
        'prompt': OpenAiChatParam(),
        # add custom config specs
        "keep_columns_tags": BoolParam(default_value=False, human_name="Keep columns tags",
                                       short_description="If true, the columns tags are kept in the output table for columns that have the same names."),
        "keep_rows_tags": BoolParam(default_value=False, human_name="Keep rows tags",
                                    short_description="If true, the rows tags are kept in the output table for rows that have the same names."),
    }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        chat: OpenAiChat = params.get_value('prompt')

        ai_transformer = AITableTransformer(inputs["source"], chat,
                                            params.get_value("keep_columns_tags"),
                                            params.get_value("keep_rows_tags"),
                                            self.message_dispatcher)
        table: Table = ai_transformer.run()

        # save the new config with the new prompt
        params.set_value('prompt', ai_transformer.chat)
        params.save_params()

        generated_text = Text(ai_transformer.generate_agent_code())
        generated_text.name = "Table transformation code"

        return {'target': table, 'generated_code': generated_text}

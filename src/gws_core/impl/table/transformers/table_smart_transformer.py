# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from pandas import DataFrame

from gws_core.config.config_types import ConfigParams, ConfigSpecs
from gws_core.config.param.param_spec import BoolParam
from gws_core.impl.openai.open_ai_helper import OpenAiHelper
from gws_core.impl.openai.smart_task_base import SmartTaskBase
from gws_core.impl.table.table import Table
from gws_core.impl.text.text import Text
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_spec_helper import InputSpecs, OutputSpecs
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs


@task_decorator("SmartTableTransformer", human_name="Smart table transformer",
                short_description="Table transformer that uses AI  (OpenAI).")
class TableSmartTransformer(SmartTaskBase):
    """
This task is still in beta version.

This task uses openAI API to generate python code that transforms a dataframe. This code is then automatically executed.

/!\ This task does not support table tags.

The data of the table is not transferered to OpenAI, only the provided text.
    """

    input_specs: InputSpecs = {
        'source': InputSpec(Table),
    }
    output_specs: OutputSpecs = {
        'target': OutputSpec(Table),
        'generated_code': SmartTaskBase.generated_code_output
    }
    config_specs: ConfigSpecs = {
        **SmartTaskBase.config_specs,
        "keep_columns_tags": BoolParam(default_value=False, human_name="Keep columns tags",
                                       short_description="If true, the columns tags are kept in the output table for columns that have the same names."),
        "keep_rows_tags": BoolParam(default_value=False, human_name="Keep rows tags",
                                    short_description="If true, the rows tags are kept in the output table for rows that have the same names."),
    }

    def get_context(self, params: ConfigParams, inputs: TaskInputs) -> str:
        # get the table
        source: Table = inputs["source"]

        context = "Your are a developer assistant that generate code in python to transform a dataframe."
        context += "The variable named 'source' contains the dataframe."
        context += "The transformed dataframe must be assigned to a variable named 'target'."
        context += f"{OpenAiHelper.generate_code_rules}"
        context += f"The dataframe has {source.nb_rows} rows and {source.nb_columns} columns."

        return context

    def build_openai_code_inputs(self, params: ConfigParams, inputs: TaskInputs) -> dict:
        # get the table
        source: Table = inputs["source"]
        return {"source": source.get_data()}

    def build_task_outputs(self, params: ConfigParams, inputs: TaskInputs,
                           code_outputs: dict, generated_code: str) -> dict:
        output = code_outputs.get("target", None)

        if output is None:
            raise Exception("The code did not generate any output")

        if not isinstance(output, DataFrame):
            raise Exception("The output must be a pandas DataFrame")

        # make the output code compatible with the live task
        live_task_code = f"""
from gws_core import Table
# keep the original table
source_table = source
# retrieve the dataframe for the generated code
source = source.get_data()
{generated_code}
# convert the dataframe to a table
target = Table(target)"""

        result = Table(output)
        # get the table
        source: Table = inputs["source"]

        if params.get_value("keep_columns_tags"):
            result.copy_column_tags_by_name(source)
            live_task_code += "\ntarget.copy_column_tags_by_name(source_table)"

        if params.get_value("keep_rows_tags"):
            result.copy_row_tags_by_name(source)
            live_task_code += "\ntarget.copy_row_tags_by_name(source_table)"

        return {'target': result, 'generated_code': Text(live_task_code)}

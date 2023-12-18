# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Any, Dict, List

from pandas import DataFrame

from gws_core.config.config_params import ConfigParams
from gws_core.config.config_types import ConfigSpecs
from gws_core.config.param.param_spec import BoolParam
from gws_core.core.utils.gws_core_packages import GwsCorePackages
from gws_core.impl.openai.smart_task_base import SmartTaskBase
from gws_core.impl.table.table import Table
from gws_core.impl.text.text import Text
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs


@task_decorator("SmartTableTransformer", human_name="Smart table transformer",
                short_description="Table transformer that uses AI  (OpenAI).")
class TableSmartTransformer(SmartTaskBase):
    """
This task is still in beta version.

This task uses openAI API to generate python code that transforms a dataframe. This code is then automatically executed.

The data of the table is not transferered to OpenAI, only the provided text.
    """

    input_specs: InputSpecs = InputSpecs({
        'source': InputSpec(Table),
    })
    output_specs: OutputSpecs = OutputSpecs({
        'target': OutputSpec(Table),
        'generated_code': SmartTaskBase.generated_code_output
    })
    config_specs: ConfigSpecs = {
        # get the openAI config specs
        **SmartTaskBase.config_specs,
        # add custom config specs
        "keep_columns_tags": BoolParam(default_value=False, human_name="Keep columns tags",
                                       short_description="If true, the columns tags are kept in the output table for columns that have the same names."),
        "keep_rows_tags": BoolParam(default_value=False, human_name="Keep rows tags",
                                    short_description="If true, the rows tags are kept in the output table for rows that have the same names."),
    }

    def build_main_context(self, params: ConfigParams, task_inputs: TaskInputs,
                           code_inputs: Dict[str, Any]) -> str:
        # prepare the input
        table: Table = task_inputs["source"]

        return f"""{self.VAR_PY_INTRO}
The code purpose is to modify a dataframe.
{self.VAR_INPUTS}
The dataframe has {table.nb_rows} rows and {table.nb_columns} columns.
{self.VAR_OUTPUTS}
{self.VAR_CODE_RULES}"""

    def build_code_inputs(self, params: ConfigParams, task_inputs: TaskInputs) -> dict:
        # get the table
        source: Table = task_inputs["source"]
        # pass the dataframe as input
        return {"source": source.get_data()}

    def get_code_expected_output_types(self) -> Dict[str, Any]:
        return {"target": DataFrame}

    def get_available_package_names(self) -> List[str]:
        return [GwsCorePackages.PANDAS, GwsCorePackages.NUMPY, GwsCorePackages.PLOTLY]

    def build_task_outputs(self, code_outputs: dict, generated_code: str,
                           params: ConfigParams, task_inputs: TaskInputs) -> dict:
        output = code_outputs.get("target", None)

        if output is None:
            raise Exception("The code did not generate any output")

        if not isinstance(output, DataFrame):
            raise Exception("The output must be a pandas DataFrame")

        # make the output code compatible with the live task
        live_task_code = f"""
from gws_core import Table
# keep the original table
source_table = sources[0]
# retrieve the dataframe for the generated code
source = sources[0].get_data()
{generated_code}
# convert the dataframe to a table
table_target = Table(target)
"""

        result = Table(output)
        # get the table
        source: Table = task_inputs["source"]

        # manager the tags options
        if params.get_value("keep_columns_tags"):
            # copy the tags from the source table to the target table
            result.copy_column_tags_by_name(source)
            # update the live task code to copy the tags
            live_task_code += "\ntable_target.copy_column_tags_by_name(source_table)"

        if params.get_value("keep_rows_tags"):
            result.copy_row_tags_by_name(source)
            live_task_code += "\ntable_target.copy_row_tags_by_name(source_table)"

        # set an the output as array
        live_task_code += "\ntargets = [table_target]"

        generated_text = Text(live_task_code)
        generated_text.name = "Table transformation code"

        return {'target': result, 'generated_code': generated_text}

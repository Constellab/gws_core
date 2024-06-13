

from typing import Any, Dict, List, Type

from pandas import DataFrame

from gws_core.config.config_params import ConfigParams
from gws_core.core.utils.gws_core_packages import GwsCorePackages
from gws_core.impl.openai.open_ai_helper import OpenAiHelper
from gws_core.impl.openai.smart_task_base import SmartTaskBase
from gws_core.impl.table.table import Table
from gws_core.io.dynamic_io import DynamicInputs, DynamicOutputs
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.resource_set.resource_list import ResourceList
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs


@task_decorator("MultiTableSmartTransformer", human_name="Smart multi tables transformer",
                short_description="Multi tables transformer that uses AI (OpenAI).",
                style=TypingStyle.material_icon("auto_awesome"))
class MultiTableSmartTransformer(SmartTaskBase):
    """
This task is still in beta version.

This task uses openAI API to generate python code that transforms multiple dataframe. This code is then automatically executed.

/!\ This task does not support table tags.

The data of the table is not transferered to OpenAI, only the provided text.
    """

    input_specs: InputSpecs = DynamicInputs({
        'source': InputSpec(Table),
    }, additionnal_port_spec=InputSpec(Table))

    output_specs: OutputSpecs = DynamicOutputs({
        'target': OutputSpec(Table),
    }, additionnal_port_spec=OutputSpec(Table))

    def build_main_context(self, params: ConfigParams, task_inputs: TaskInputs,
                           code_inputs: Dict[str, Any]) -> str:
        # prepare the input
        resource_list: ResourceList = task_inputs["source"]

        return f"""{self.VAR_PY_INTRO}
The code purpose is to modify multiple dataframes.
{self.VAR_INPUTS}
There are {len(resource_list)} dataframes in the list.
{self.VAR_OUTPUTS}
{self.VAR_CODE_RULES}"""

    def build_code_inputs(self, params: ConfigParams, task_inputs: TaskInputs) -> dict:
        # get the table
        resource_list: ResourceList = task_inputs["source"]

        dataframes: List[DataFrame] = []
        i = 0
        for resource in resource_list:
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

    def build_task_outputs(self, code_outputs: dict, generated_code: str,
                           params: ConfigParams, task_inputs: TaskInputs) -> dict:
        output: List[DataFrame] = code_outputs.get("target", None)

        if output is None:
            raise Exception("The code did not generate any output")

        if not isinstance(output, list):
            raise Exception("The output must be a list of pandas DataFrame")

        # make the output code compatible with the live task
        # Only print the code that is generated
        live_task_code = f"""
##################### LIVE TASK CODE #####################
from gws_core import Table
# keep the original table
# retrieve the dataframe for the generated code
source = [s.get_data() for s in sources]
{generated_code}
# convert the dataframe to a table
targets = [Table(t) for t in target]
##################### LIVE TASK CODE #####################
"""
        self.log_info_message(live_task_code)

        resource_list = ResourceList()

        for dataframe in output:
            resource_list.add_resource(Table(dataframe))

        return {'target': resource_list}

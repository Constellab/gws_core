# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, Dict, List

from gws_core.config.config_params import ConfigParams
from gws_core.core.utils.gws_core_packages import GwsCorePackages
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file import File
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.openai.smart_task_base import SmartTaskBase
from gws_core.impl.table.table import Table
from gws_core.impl.text.text import Text
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs


@task_decorator("SmartPlot", human_name="Smart plot generator",
                short_description="Generate a plot using an AI (OpenAI).")
class SmartPlot(SmartTaskBase):
    """
This task is still in beta version.

This task uses openAI API to generate python code that generate a chart using matplotlib library. This code is then automaticaaly executed.

/!\ This task does not support table tags.

The data of the table is not transferered to OpenAI, only the provided text.
    """

    input_specs: InputSpecs = InputSpecs({
        'source': InputSpec(Table),
    })
    output_specs: OutputSpecs = OutputSpecs({
        'target': OutputSpec(File, human_name='Plot', short_description='Generated plot file by the AI.'),
        'generated_code': SmartTaskBase.generated_code_output
    })

    temp_dir: str
    ouput_path: str

    def build_main_context(self, params: ConfigParams, task_inputs: TaskInputs,
                           code_inputs: Dict[str, Any]) -> str:
        table: Table = task_inputs["source"]

        return f"""{self.VAR_PY_INTRO}
The code purpose is to modify generate a plot file from a DataFrame using matplotlib.
{self.VAR_INPUTS}
The dataframe has {table.nb_rows} rows and {table.nb_columns} columns.
The variable named 'output_path' contains the absolute path of the output png file destination. Don't use the show method.
{self.VAR_CODE_RULES}"""

    def get_code_expected_output_types(self) -> Dict[str, Any]:
        return {}

    def get_available_package_names(self) -> List[str]:
        return [GwsCorePackages.PANDAS, GwsCorePackages.NUMPY, GwsCorePackages.MATPLOTLIB]

    def build_code_inputs(self, params: ConfigParams, task_inputs: TaskInputs) -> dict:
        # prepare the input
        table: Table = task_inputs["source"]

        # execute the live code
        self.temp_dir = Settings.make_temp_dir()
        self.ouput_path = self.temp_dir + "/output.png"

        # all variable accessible in the generated code
        return {"source": table.get_data(), 'output_path': self.ouput_path}

    def build_task_outputs(self, code_outputs: dict, generated_code: str,
                           params: ConfigParams, task_inputs: TaskInputs) -> dict:
        if not FileHelper.exists_on_os(self.ouput_path) or not FileHelper.is_file(self.ouput_path):
            raise Exception("The output must be a file")

        # make the output code compatible with the live task
        live_task_code = f"""
from gws_core import File
import os
source = sources[0].get_data()
# generate the output file path
output_path = os.path.join(working_dir, 'output.png')
{generated_code}
targets = [File(output_path)]"""

        generated_text = Text(live_task_code)
        generated_text.name = "Plot code"

        return {'target': File(self.ouput_path), 'generated_code': generated_text}

    def run_after_task(self) -> None:
        FileHelper.delete_dir(self.temp_dir)

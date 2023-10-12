# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.config.config_params import ConfigParams
from gws_core.config.config_types import ConfigSpecs
from gws_core.core.utils.gws_core_packages import GwsCorePackages
from gws_core.core.utils.json_helper import JSONHelper
from gws_core.impl.json.json_dict import JSONDict
from gws_core.impl.openai.open_ai_helper import OpenAiHelper
from gws_core.impl.openai.smart_task_base import SmartTaskBase
from gws_core.impl.text.text import Text
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs


@task_decorator("SmartJsonTransformer", human_name="Smart json transformer",
                short_description="Json transformer that uses AI  (OpenAI).")
class JsonSmartTransformer(SmartTaskBase):
    """
This task is still in beta version.

This task uses openAI API to generate python code that transforms a json. This code is then automatically executed.

The structure of the json is transfered to OpenAI, not the json itself.
    """

    input_specs: InputSpecs = InputSpecs({
        'source': InputSpec(JSONDict),
    })
    output_specs: OutputSpecs = OutputSpecs({
        'target': OutputSpec(JSONDict),
        'generated_code': SmartTaskBase.generated_code_output
    })
    config_specs: ConfigSpecs = {
        **SmartTaskBase.config_specs,
    }

    def get_context(self, params: ConfigParams, inputs: TaskInputs) -> str:
        # get the table
        source: JSONDict = inputs["source"]

        json_structure = JSONHelper.extract_json_structure(source.get_data())
        str_json_structure = JSONHelper.safe_dumps(json_structure)

        context = "You are a developer assistant that generate code in python to modify a json dict object."
        # context = "You are a developer assistant tasked with modifying a Python dictionary (variable named 'source') that adheres to the following JSON schema:"
        context += "\nUse variable named 'source' as input. Do not create it. The 'source' variable is a dictionary with the following schema : "
        context += f"\n```{str_json_structure}```\n"
        context += "\nThe transformed json object must be assigned to a variable named 'target' and be a python dictionary."
        context += f"\n{OpenAiHelper.get_code_context([GwsCorePackages.NUMPY])}"
        # context += f"\nHere is the json schema of the source json object : ```{str_json_structure}```"
  # You are a developer assistant tasked with modifying a Python dictionary (named 'source') that adheres to the following JSON schema:
        return context

    def build_openai_code_inputs(self, params: ConfigParams, inputs: TaskInputs) -> dict:
        # get the table
        source: JSONDict = inputs["source"]
        return {"source": source.get_data()}

    def build_task_outputs(self, params: ConfigParams, inputs: TaskInputs,
                           code_outputs: dict, generated_code: str) -> dict:
        output = code_outputs.get("target", None)

        if output is None:
            raise Exception("The code did not generate any output")

        # make the output code compatible with the live task
        live_task_code = f"""
from gws_core import JSONDict
# retrieve the json for the generated code
source = sources[0].get_data()
{generated_code}
# convert the target to a JSONDict and put it in targets
targets = [JSONDict(target)]
"""

        result = JSONDict(output)

        generated_text = Text(live_task_code)
        generated_text.name = "JSON transformation code"

        return {'target': result, 'generated_code': generated_text}

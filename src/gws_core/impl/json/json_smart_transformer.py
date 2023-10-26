# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Any, Dict, List, Type

from gws_core.config.config_params import ConfigParams
from gws_core.config.config_types import ConfigSpecs
from gws_core.core.utils.gws_core_packages import GwsCorePackages
from gws_core.core.utils.json_helper import JSONHelper
from gws_core.impl.json.json_dict import JSONDict
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

    def build_main_context(self, params: ConfigParams, task_inputs: TaskInputs,
                           code_inputs: Dict[str, Any]) -> str:
        # return "The code purpose is to modify a json dict object."

        # get the structure of the json
        json_structure = JSONHelper.extract_json_structure(code_inputs)
        str_json_structure = JSONHelper.safe_dumps(json_structure)

        return f"""{self.PY_INTRO}
The code purpose is to modify a json dict object.
{self.VAR_INPUTS}
The 'source' dict has the following schema :
```{str_json_structure}```.
{self.VAR_OUTPUTS}
{self.VAR_CODE_RULES}"""

    def build_code_inputs(self, params: ConfigParams, task_inputs: TaskInputs) -> dict:
        # get the dict as source
        source: JSONDict = task_inputs["source"]
        return {"source": source.get_data()}

    def get_code_expected_output_types(self) -> Dict[str, Type]:
        return {'target': dict}

    def get_available_package_names(self) -> List[str]:
        return [GwsCorePackages.NUMPY]

    def build_task_outputs(self, code_outputs: dict, generated_code: str,
                           params: ConfigParams, task_inputs: TaskInputs) -> dict:
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

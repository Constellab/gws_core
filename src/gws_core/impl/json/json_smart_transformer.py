from typing import Dict, List, Type

from gws_core.config.config_params import ConfigParams
from gws_core.config.config_specs import ConfigSpecs
from gws_core.core.utils.gws_core_packages import GwsCorePackages
from gws_core.core.utils.json_helper import JSONHelper
from gws_core.impl.json.json_dict import JSONDict
from gws_core.impl.openai.ai_prompt_code import AIPromptCode, AIPromptCodeContext
from gws_core.impl.openai.open_ai_chat import OpenAiChat
from gws_core.impl.openai.open_ai_chat_param import OpenAiChatParam
from gws_core.impl.text.text import Text
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.model.typing_style import TypingStyle
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs


class AIJsonTransformer(AIPromptCode):
    """Class to call AI to generate a python code that transforms a json.
    The structure of the json is transfered to OpenAI, not the json itself.
    """

    json_: dict

    def __init__(self, json_: dict, chat: OpenAiChat, message_dispatcher=None):
        super().__init__(chat, message_dispatcher)
        self.json_ = json_

    def build_main_context(self, context: AIPromptCodeContext) -> str:
        # return "The code purpose is to modify a json dict object."

        # get the structure of the json
        json_structure = JSONHelper.extract_json_structure(self.json_)
        str_json_structure = JSONHelper.safe_dumps(json_structure)

        return f"""{context.python_code_intro}
The code purpose is to modify a json dict object.
{context.inputs_description}
The 'source' dict has the following schema :
```{str_json_structure}```.
{context.outputs_description}
{context.code_rules}"""

    def build_code_inputs(self) -> dict:
        # get the dict as source
        return {"source": self.json_}

    def get_code_expected_output_types(self) -> Dict[str, Type]:
        return {"target": dict}

    def get_available_package_names(self) -> List[str]:
        return [GwsCorePackages.NUMPY]

    def build_output(self, code_outputs: dict) -> dict:
        output = code_outputs.get("target", None)

        if output is None:
            raise Exception("The code did not generate any output")

        if not isinstance(output, dict):
            raise Exception("The generated output is not a dict")

        return output

    def _generate_agent_code(self, generated_code):
        return f"""
from gws_core import JSONDict
# retrieve the json for the generated code
source = sources[0].get_data()
{generated_code}
# convert the target to a JSONDict and put it in targets
targets = [JSONDict(target)]
"""


@task_decorator(
    "SmartJsonTransformer",
    human_name="Smart json transformer",
    short_description="Json transformer that uses AI  (OpenAI).",
    style=TypingStyle.material_icon("auto_awesome"),
)
class JsonSmartTransformer(Task):
    """
    This task uses openAI API to generate python code that transforms a json.
    This code is then automatically executed to apply transformation on the input json.

    The structure of the json is transfered to OpenAI, not the json itself.

    This is useful when you want to transform a json in a way that is not trivial.
    """

    input_specs: InputSpecs = InputSpecs(
        {
            "source": InputSpec(JSONDict),
        }
    )
    output_specs: OutputSpecs = OutputSpecs(
        {
            "target": OutputSpec(JSONDict),
            "generated_code": AIJsonTransformer.generate_agent_code_task_output_config(),
        }
    )
    config_specs = ConfigSpecs({"prompt": OpenAiChatParam()})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        chat: OpenAiChat = params.get_value("prompt")

        json_dict: JSONDict = inputs["source"]

        json_transformer = AIJsonTransformer(json_dict.get_data(), chat, self.message_dispatcher)
        result: dict = json_transformer.run()

        # save the new config with the new prompt
        params.set_value("prompt", json_transformer.chat)
        params.save_params()

        generated_text = Text(json_transformer.generate_agent_code())
        generated_text.name = "JSON transformation code"

        return {"target": JSONDict(result), "generated_code": generated_text}

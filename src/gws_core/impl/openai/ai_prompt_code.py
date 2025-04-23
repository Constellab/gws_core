

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Type

from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.impl.agent.helper.agent_code_helper import AgentCodeHelper
from gws_core.impl.openai.open_ai_chat import OpenAiChat
from gws_core.impl.openai.open_ai_helper import OpenAiHelper
from gws_core.impl.text.text import Text
from gws_core.io.io_spec import OutputSpec


class AIPromptCodeContext(BaseModelDTO):
    """ Class that contains the prompt parts to build a prompt for the AI with AIPromptCode.
    """
    python_code_intro: str
    r_code_intro: str
    inputs_description: Optional[str]
    outputs_description: Optional[str]
    code_rules: Optional[str]


class AIPromptCode():
    """Base class to apply transformation to object (like resource) based on a prompt and AI (openAI).
    This will ask the AI to generate a code and then execute it.
    This class helps describe the input, output and prompt to the AI, and then execute the generated code.
    THe data is not transfered to OpenAI, only the provided text.

    This class need a context to tell the AI what is the goal of the task, what are the inputs and outputs...
    To build the context, you must overide the following methods (see build_context method to view the context structure):

    - build_main_context: method to build the context of the openAI chat. This context is used to give precise information to the AI to generate the code you want.
    - build_code_inputs: method to build the variables that will be accessible in the generated code.
    - get_code_expected_output_types: method to describe the output names (keys) and types (values) expected by the generated code.
    - get_available_package_names: method to retrieve the package names that can be used by the AI in the generated the code.

    Once the code is generated, it is executed and the outputs are retrieved. You will need to convert the code
    outputs to task outputs. To do so, you must overide the following method:

    - build_task_outputs: method to build the task outputs resources based on the generated code outputs.
    """
    PROMPT_PY_INTRO = "You are a developer assistant that generate code in python."
    PROMPT_R_INTRO = "You are a developer assistant that generate code in R."

    chat: OpenAiChat = None
    message_dispatcher: MessageDispatcher = None

    def __init__(self, chat: OpenAiChat, message_dispatcher: Optional[MessageDispatcher] = None):
        self.chat = chat

        if message_dispatcher is None:
            self.message_dispatcher = MessageDispatcher()
        else:
            self.message_dispatcher = message_dispatcher

    @abstractmethod
    def build_main_context(self, context: AIPromptCodeContext) -> str:
        """Method to build the context of the openAI chat. This should define the main goal of the task.
        You can use context variable to build main context.

        The recommended order is :
        - INTRO
        - Text to explain the goal of the task (Ex: "The code purpose is to generate a plotly express figure from a DataFrame.")
        - INPUTS
        - OUTPUTS
        - CODE_RULES

        You can insert text after a variable to add more information, like :
        - inputs_description + 'The dataframe has ' + str(table.nb_rows) + ' rows and ' + str(table.nb_columns) + ' columns.'
        - outputs_description + 'Only build the figure object, do not display the figure using 'show' method.'

        :param context: the variables to build the context
        :type context: AIPromptCodeVariables
        :return: the context
        :rtype: str
        """

    @abstractmethod
    def build_code_inputs(self) -> dict:
        """Method to build the variables that will be accessible in the generated code.
        It is recommended to use known object types for the inputs, like dict, list, Dataframe, int ...
        so the AI can understand the structure of the input.

        :return: the input dict that will be accessible in the generated code
        :rtype: dict
        """

    @abstractmethod
    def get_code_expected_output_types(self) -> Dict[str, Type]:
        """Method to describe the output names (keys) and types (values) expected by the generated code.
        The AI will receive instructions to generate code that returns variables with the specified names and types.
        This is used by build_task_outputs to retrieve the output of the generated code.

        :return: the output specs
        :rtype: Dict[str, Type]
        """
        return {}

    @abstractmethod
    def get_available_package_names(self) -> List[str]:
        """Method to retrieve the package names that can be used by the AI in the generated the code.
        The package must be installed in the lab.
        This is used by build_code_context to retrieve the version of the package are write a text to describe the packages.
        Return empty list if no package is needed.

        :return: the list of package names
        :rtype: List[str]
        """
        return []

    @abstractmethod
    def build_output(self, code_outputs: Dict[str, Any]) -> Any:
        """Method to build the output based on the generated code outputs.

        :param code_outputs: the outputs of the generated code
        :type code_outputs: dict
        :return: the task outputs
        :rtype: dict
        """

    @abstractmethod
    def _generate_agent_code(self, generated_code: str) -> str:
        """Generate the agent code that will be used to run the code in the agent.

        :param generated_code: the code generated by the AI
        :type generated_code: str
        :return: the agent code
        :rtype: str
        """

    def build_inputs_context(self, code_inputs: Dict[str, Any]) -> str:
        """Method that is automatically called by the task to describe the inputs that are accessible in the generated code.
        This method can be overrided to change the way of describing the inputs, or to add more information
        (like the number of rows for a dataframe, the structure of a json ...)
        :param inputs: transformed inputs generated by build_code_inputs method
        :type inputs: dict
        :return: the description of the inputs to be passed to the context
        :rtype: str
        """
        if len(code_inputs) == 0:
            return ""
        return OpenAiHelper.describe_inputs_for_context(code_inputs)

    def build_outputs_context(self) -> str:
        """Method that is automatically called by the task to describe the outputs that are accessible in the generated code.
        This method can be overrided to change the way of describing the outputs.
        :param outputs_specs: the outputs specs
        :type outputs_specs: Dict[str, Type]
        :return: the description of the outputs to be passed to the context
        :rtype: str
        """
        output_specs = self.get_code_expected_output_types()
        if len(output_specs) == 0:
            return ""
        return OpenAiHelper.describe_outputs_for_context(output_specs)

    def build_code_rules_context(self, pip_package_names: List[str] = None) -> str:
        """Method to define the context rules for the code generation, so the generated code is executable.
        This method can be overrided to change the way of describing the code context.
        :param pip_package_names: list of available package that can be used in the generated code. The version of the package will be automatically retrieved, defaults to None
        :type pip_package_names: List[str], optional
        :return: the context
        :rtype: str
        """
        return OpenAiHelper.get_code_context(pip_package_names)

    def build_context(self, code_inputs: Dict[str, Any]) -> str:
        """Method that is automatically called by the task to build the context.
        This method can be overided to change the way of describing the context.

        :return: the context
        :rtype: str
        """

        inputs_description = self.build_inputs_context(code_inputs) or ''

        outputs_description = self.build_outputs_context() or ''

        code_rules = self.build_code_rules_context(self.get_available_package_names()) or ''

        variables = AIPromptCodeContext(
            python_code_intro=self.PROMPT_PY_INTRO,
            r_code_intro=self.PROMPT_R_INTRO,
            inputs_description=inputs_description,
            outputs_description=outputs_description,
            code_rules=code_rules
        )

        # retrieve the main context
        main_context = self.build_main_context(variables)
        if not main_context or len(main_context) == 0:
            raise Exception("The main context must be defined")

        return main_context

    def run(self) -> Any:
        # all variable accessible in the generated code
        code_inputs = self.build_code_inputs()

        if self.chat.last_message_is_user():
            # retrieve the main context
            context = self.build_context(code_inputs)

            # Store the context in the chat object
            self.chat.set_system_prompt(context)

            # only call open ai if the last message is from the user
            # create the completion
            self.message_dispatcher.notify_info_message('Generating code snippet...')
            self.chat.call_gpt()

        else:
            self.message_dispatcher.notify_info_message('The last message is not from the user, no need to call openAI')

        code = self.chat.get_last_assistant_message(extract_code=True)
        if code is None:
            raise Exception("No code generated by OpenAI")

        self.message_dispatcher.notify_info_message('Code generated by OpenAI: ' + code)

        # execute the live code
        self.message_dispatcher.notify_info_message('Executing the code snippet...')
        outputs = AgentCodeHelper.run_python_code(code, code_inputs)

        return self.build_output(outputs)

    def generate_agent_code(self) -> str:
        """Generate the agent code that will be used to run the code in the agent.

        :return: the agent code
        :rtype: str
        """

        last_assistant_message = self.chat.get_last_assistant_message(extract_code=True)
        if last_assistant_message is None:
            raise Exception("No code generated by OpenAI")

        return self._generate_agent_code(last_assistant_message)

    @staticmethod
    def generate_agent_code_task_output_config() -> OutputSpec:
        """Get the task output config for the generate_agent_code task.

        :return: the task output config
        :rtype: Dict[str, Any]
        """
        return OutputSpec(
            Text, human_name='Generated code',
            short_description='Modified generated code that can be used in a python agent directly.')

# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, List

import openai

from gws_core.core.utils.settings import Settings
from gws_core.impl.openai.open_ai_chat import OpenAiChat

openai.api_key = "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"


class OpenAiHelper():

    generate_code_rules = "Don't prompt the method signature. Write comments for the code. Generate only 1 block of code between ``` characters."

    @classmethod
    def call_gpt(cls, chat: OpenAiChat) -> OpenAiChat:
        """Call gpt chat, and add the response to the chat object as an assistant message

        :param chat: _description_
        :type chat: OpenAiChat
        :return: _description_
        :rtype: OpenAiChat
        """

        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=chat.export_gpt_messages()
        )

        chat.add_assistant_message(completion.choices[0].message.content)

        return chat

    @classmethod
    def get_code_context(cls, pip_package_names: List[str] = None) -> str:
        """Define the context rules for the code generation, so the generated code is executable.

        :param pip_package_names: list of available package that can be used in the generated code. The version of the package will be automatically retrieved, defaults to None
        :type pip_package_names: List[str], optional
        :return: the context
        :rtype: str
        """
        packages_context = OpenAiHelper.get_package_version_context(pip_package_names)
        return f"{packages_context}\n{OpenAiHelper.generate_code_rules}"

    @classmethod
    def get_package_version_context(cls, pip_package_names: List[str]) -> str:
        """
        Method to improve the context by giving the version of the provided pip packages
        installed in the lab.
        """
        if pip_package_names is None:
            return ""
        packages = Settings.get_instance().get_pip_packages(pip_package_names)

        if len(packages) == 0:
            return ""

        packages_text: List[str] = []
        for package in packages:
            packages_text.append(f"{package.name}=={package.version}")

        return f"The following packages with versions are installed : {', '.join(packages_text)}. The packages must be imported if needed."

    @classmethod
    def describe_inputs_for_context(cls, inputs: dict) -> str:
        inputs_texts: List[str] = []
        for key, value in inputs.items():
            # TODO use the type to string in UTILS
            inputs_texts.append(f"'{key}' (type '{value.__class__.__name__}')")

        return f"You have access to the following input variables : {', '.join(inputs_texts)}. The input variables are already initialized, do not create them."

    @classmethod
    def describe_outputs_for_context(cls, outputs_specs: Dict[str, type]) -> str:
        outputs_texts: List[str] = []
        for key, value in outputs_specs.items():
            # TODO use the type to string in UTILS
            outputs_texts.append(f"'{key}' (type '{value.__name__}')")

        return f"You must assigne the result to the following output variables : {', '.join(outputs_texts)}."

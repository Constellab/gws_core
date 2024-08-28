

from typing import Dict, List, Optional

from openai import OpenAI

from gws_core.core.utils.settings import Settings
from gws_core.core.utils.utils import Utils
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.openai.open_ai_types import OpenAiChatMessage


class OpenAiHelper():

    generate_code_rules = "Don't prompt the method signature. Write comments for the code. Generate only 1 block of code between ``` characters."

    whiper_max_file_size = 10 * 1024 * 1024  # 10MB

    @classmethod
    def call_gpt(cls, chat_messages: List[OpenAiChatMessage]) -> str:
        """Call gpt chat, and add the response to the chat object as an assistant message

        :param chat_messages: list of messages and context to send to the AI
        :type chat_messages: OpenAiChat
        :return: _description_
        :rtype: OpenAiChat
        """
        client = OpenAI(api_key=Settings.get_open_ai_api_key())

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=chat_messages
        )

        return response.choices[0].message.content

    @classmethod
    def get_code_context(cls, pip_package_names: List[str] = None) -> str:
        """Define the context rules for the code generation, so the generated code is executable.

        :param pip_package_names: list of available package that can be used in the generated code. The version of the package will be automatically retrieved, defaults to None
        :type pip_package_names: List[str], optional
        :return: the context
        :rtype: str
        """
        packages_context = OpenAiHelper.get_package_version_context(
            pip_package_names)
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
            inputs_texts.append(
                f"'{key}' (type '{Utils.stringify_type(type(value), True)}')")

        return cls.describe_inputs_text_for_context(str({', '.join(inputs_texts)}))

    @classmethod
    def describe_inputs_text_for_context(cls, input_description: str) -> str:
        return f"You have access to the following input variables : {input_description}. The input variables are already initialized, do not create them."

    @classmethod
    def describe_outputs_for_context(cls, outputs_specs: Dict[str, type]) -> str:
        outputs_texts: List[str] = []
        for key, value in outputs_specs.items():
            outputs_texts.append(
                f"'{key}' (type '{Utils.stringify_type(value, True)}')")

        return cls.describe_outputs_text_for_context(str({', '.join(outputs_texts)}))

    @classmethod
    def describe_outputs_text_for_context(cls, output_description: str) -> str:
        return f"You must assigne the result to the following output variables : {output_description}."

    @classmethod
    def call_whisper(cls, audio_file_path: str, prompt: Optional[str] = None) -> str:
        """Call whisper to transcribe an audio file

        :param audio_file_path: path to the audio file
        :type audio_file_path: str
        :return: the transcription
        :rtype: str
        """
        if not FileHelper.exists_on_os(audio_file_path):
            raise FileNotFoundError(f"The file '{audio_file_path}' does not exist.")

        if FileHelper.get_size(audio_file_path) > cls.whiper_max_file_size:
            raise Exception(f"The file '{audio_file_path}' is too large. The maximum file size is 10MB.")

        client = OpenAI(api_key=Settings.get_open_ai_api_key())

        with open(audio_file_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                prompt=prompt,
            )

        return transcription.text

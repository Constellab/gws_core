from json import loads

from fastapi import UploadFile

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.utils.logger import Logger
from gws_core.impl.openai.open_ai_chat import OpenAiChat
from gws_core.impl.openai.open_ai_helper import OpenAiHelper
from gws_core.impl.openai.open_ai_transcription_service import OpenAiTranscriptionService
from gws_core.impl.rich_text.block.rich_text_block_header import RichTextBlockHeaderLevel
from gws_core.impl.rich_text.block.rich_text_block_list import RichTextBlockList
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_types import RichTextBlock


class TranscriptionOutput(BaseModelDTO):
    type: str
    data: dict


class RichTextTranscriptionService:
    """Service to transcribe an audio file to a rich text"""

    prompt = """

You are an assistant who takes a text transcription and converts it into structured JSON based on commands.

Handle synonyms and different languages to recognize commands.
There might be no command in the transcription, return a default paragraph block.
If there is no text in the transcription, return an empy array.
If you don't recognize a command or have a doubt, return a default paragraph block.
An end of the command might be written by the user (like 'end title'), but it's not mandatory.
Don't write the name of the command in the transcription, only the content.
Don't change the text of the transcription, only the structure, keep the original language.
Return only the json array without carry return, not the full response.

Here is a json schema that describes the commands.
The generated JSON must validate this schema.
```
{{SCHEMA}}
```
"""

    json_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "array",
        "items": {
            "oneOf": [
                {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": ["paragraph"]},
                        "command": {"type": "string", "enum": ["No command, default"]},
                        "data": {
                            "type": "object",
                            "properties": {
                                "text": {
                                    "type": "string",
                                    "description": "The text of the paragraph. Capitalize the first letter of the first word.",
                                }
                            },
                        },
                    },
                    "required": ["type", "command", "data"],
                },
                {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": ["title"]},
                        "command": {"type": "string", "enum": ["title", "header"]},
                        "data": {
                            "type": "object",
                            "properties": {
                                "level": {
                                    "type": "integer",
                                    "enum": [1, 2, 3],
                                    "description": "The level of the title. 1 is the highest level.",
                                },
                                "text": {
                                    "type": "string",
                                    "description": "The text of the title. Capitalize the first letter of the first word.",
                                },
                            },
                            "required": ["level", "text"],
                        },
                    },
                    "required": ["type", "command", "data"],
                },
                {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": ["list"]},
                        "command": {"type": "string", "enum": ["list"]},
                        "data": {
                            "type": "object",
                            "properties": {
                                "items": {
                                    "type": "array",
                                    "description": "An array of dict representing the items of the list. Can be recursive.",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "content": {
                                                "type": "string",
                                                "description": "The content of the item. Do not capitalize the first letter of the first word.",
                                            },
                                            "items": {
                                                "type": "array",
                                                "description": "An array of dict representing the sub-items of the item. Can be recursive.",
                                            },
                                        },
                                        "required": ["content", "items"],
                                    },
                                },
                                "style": {"type": "string", "enum": ["ordered", "unordered"]},
                            },
                            "required": ["items", "style"],
                        },
                    },
                    "required": ["type", "command", "data"],
                },
                {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": ["formula"]},
                        "command": {"type": "string", "enum": ["math formula"]},
                        "data": {
                            "type": "object",
                            "properties": {
                                "formula": {
                                    "type": "string",
                                    "description": "The mathemathical formula using KaTeX syntax.",
                                }
                            },
                        },
                    },
                    "required": ["type", "command", "data"],
                },
            ]
        },
    }

    @classmethod
    def transcribe_uploaded_audio_to_rich_text(cls, file: UploadFile) -> RichText:
        """Transcribe an uploaded audio file to a rich text.

        :param file: the uploaded audio file
        :type file: UploadFile
        :return: the rich text
        :rtype: RichText
        """
        transcription_text = OpenAiTranscriptionService.transcribe_uploaded_audio(file)
        return cls._transcription_text_to_rich_text(transcription_text)

    @classmethod
    def transcribe_audio_file_to_rich_text(cls, file_path: str) -> RichText:
        transcription_text = OpenAiHelper.call_whisper(file_path)
        Logger.debug(f"[RichTextTranscriptionService] Transcription text: {transcription_text}")
        return cls._transcription_text_to_rich_text(transcription_text)

    @classmethod
    def _transcription_text_to_rich_text(cls, transcription_text: str) -> RichText:
        try:
            return cls.transcribe_text_to_rich_text(transcription_text)
        # if an error occurs, return a default paragraph block
        except Exception as e:
            Logger.error(f"Error while transcribing text to rich text: {e}. Ignoring the commands.")
            rich_text = RichText()
            rich_text.add_paragraph(transcription_text)
            return rich_text

    @classmethod
    def transcribe_text_to_rich_text(cls, text: str) -> RichText:
        # apply the command in the transcription using the prompt
        transcription_dict = cls.apply_command_in_transcription(text)

        Logger.debug(f"[RichTextTranscriptionService] Transcription dict: {transcription_dict}")

        transcriptions: list[TranscriptionOutput] = TranscriptionOutput.from_json_list(
            transcription_dict
        )

        # convert the transcription to a rich text
        return cls._convert_transcriptions_to_rich_text(transcriptions)

    @classmethod
    def apply_command_in_transcription(cls, transcription_text: str) -> list[TranscriptionOutput]:
        """Convert a text transcription with commands to a rich text

        :param text: text transcription
        :type text: str
        :return: the rich text
        :rtype: str
        """

        prompt = cls.prompt.replace("{{SCHEMA}}", str(cls.json_schema))
        chat = OpenAiChat(system_prompt=prompt)
        chat.add_user_message(transcription_text)

        response = OpenAiChat.call_gpt(chat)

        return loads(response)

    @classmethod
    def _convert_transcriptions_to_rich_text(
        cls, transcriptions: list[TranscriptionOutput]
    ) -> RichText:
        """Convert a text to a rich text block

        :param text: text
        :type text: str
        :return: the rich text block
        :rtype: dict
        """

        rich_text = RichText()
        for block in transcriptions:
            cls._append_transcription_to_rich_text(rich_text, block)

        return rich_text

    @classmethod
    def _append_transcription_to_rich_text(
        cls, rich_text: RichText, transcription: TranscriptionOutput
    ) -> RichTextBlock | None:
        """Convert a text to a rich text block

        :param text: text
        :type text: str
        :return: the rich text block
        :rtype: dict
        """

        if transcription.type == "paragraph":
            return rich_text.add_paragraph(transcription.data.get("text"))
        elif transcription.type == "title":
            return rich_text.add_header(
                transcription.data.get("text"),
                RichTextBlockHeaderLevel.from_int(transcription.data.get("level", 1)),
            )
        elif transcription.type == "list":
            return rich_text.add_list(RichTextBlockList.from_json(transcription.data))
        elif transcription.type == "formula":
            return rich_text.add_formula(transcription.data.get("formula"))
        else:
            return None

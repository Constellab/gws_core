import os
import shutil

from fastapi import UploadFile

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.openai.open_ai_helper import OpenAiHelper


class TranscriptionResultDTO(BaseModelDTO):
    """Result of an audio-to-text transcription: just the transcribed text."""

    text: str


class OpenAiTranscriptionService:
    """Generic audio-to-text transcription (OpenAI Whisper).

    This is the shared building block for any AI feature that accepts voice
    input: the client records audio, posts it here to get the transcription,
    then proceeds exactly as if the user had typed that text. Keeps the 10MB
    limit, temp-file handling, and Whisper configuration in one place.

    ``RichTextTranscriptionService`` and ``FormAiFillService`` (text endpoint)
    are consumers of this pattern.
    """

    @classmethod
    def transcribe_uploaded_audio(cls, file: UploadFile) -> str:
        """Transcribe an uploaded audio file to plain text.

        Writes the upload to a temp directory, calls Whisper (which enforces
        the 10MB limit), and cleans up. Returns the raw transcription text.
        """
        tmp_dir = Settings.get_instance().make_temp_dir()
        audio_file_path = os.path.join(tmp_dir, "audio.wav")
        with open(audio_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        try:
            text = OpenAiHelper.call_whisper(audio_file_path)
        finally:
            FileHelper.delete_dir(tmp_dir)

        Logger.debug(f"[OpenAiTranscriptionService] Transcription: {text}")
        return text

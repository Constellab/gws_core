"""Generic audio-to-text transcription (OpenAiTranscriptionService)."""
import io
from unittest.mock import patch

from fastapi import UploadFile

from gws_core.impl.openai.open_ai_transcription_service import OpenAiTranscriptionService
from gws_core.test.base_test_case_light import BaseTestCaseLight

_WHISPER_TARGET = "gws_core.impl.openai.open_ai_helper.OpenAiHelper.call_whisper"


class TestOpenAiTranscription(BaseTestCaseLight):
    def test_transcribe_uploaded_audio_returns_whisper_text(self):
        upload = UploadFile(filename="audio.wav", file=io.BytesIO(b"fake-audio-bytes"))
        with patch(_WHISPER_TARGET, return_value="hello world") as whisper_mock:
            text = OpenAiTranscriptionService.transcribe_uploaded_audio(upload)
        self.assertEqual(text, "hello world")
        whisper_mock.assert_called_once()
        # The temp file path passed to Whisper should be a real .wav written from the upload.
        (called_path,), _ = whisper_mock.call_args
        self.assertTrue(called_path.endswith("audio.wav"))

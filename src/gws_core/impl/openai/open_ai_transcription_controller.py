from fastapi import File as FastAPIFile
from fastapi import UploadFile
from fastapi.param_functions import Depends

from gws_core.core_controller import core_app
from gws_core.impl.openai.open_ai_transcription_service import (
    OpenAiTranscriptionService,
    TranscriptionResultDTO,
)
from gws_core.user.authorization_service import AuthorizationService


@core_app.post(
    "/ai/transcribe-audio",
    tags=["AI"],
    summary="Transcribe an audio file to plain text (generic, for any voice-input feature)",
)
def transcribe_audio(
    file: UploadFile = FastAPIFile(...),
    _=Depends(AuthorizationService.check_user_access_token),
) -> TranscriptionResultDTO:
    """Transcribe an uploaded audio file (≤10MB) to text via OpenAI Whisper.

    Generic entry point: the client records audio, posts it here, then feeds
    the returned text to whatever AI action it wants (e.g. ``/form/{id}/fill-from-text``).
    """
    text = OpenAiTranscriptionService.transcribe_uploaded_audio(file)
    return TranscriptionResultDTO(text=text)



from datetime import datetime
from typing import Optional

from fastapi import Depends
from fastapi.responses import StreamingResponse

from gws_core.core.utils.response_helper import ResponseHelper
from gws_core.progress_bar.progress_bar_dto import \
    ProgressBarMessagesBetweenDatesDTO

from ..core_controller import core_app
from ..user.auth_service import AuthService
from .progress_bar_service import ProgressBarService


@core_app.get("/progress-bar/{id}/download", tags=["Progress bar"], summary="Get a progress bar")
def download_progress_bar(id: str,
                          _=Depends(AuthService.check_user_access_token)) -> StreamingResponse:

    logs = ProgressBarService.download_progress_bar(id=id)

    return ResponseHelper.create_file_response_from_str(logs, "messages.txt")


@core_app.get(
    "/progress-bar/{id}/messages", tags=["Progress bar"],
    summary="Get messages of a progress bar")
def get_messages(id: str,
                 nb_of_messages: Optional[int] = 20,
                 _=Depends(AuthService.check_user_access_token)) -> ProgressBarMessagesBetweenDatesDTO:
    """Get last progress bar messages
    """

    return ProgressBarService.get_progress_bar_messages(id=id, nb_of_messages=nb_of_messages)


@core_app.get(
    "/progress-bar/{id}/messages/{from_datetime}", tags=["Progress bar"],
    summary="Get messages of a progress bar")
def get_messages_from_date(id: str,
                           from_datetime: Optional[datetime],
                           nb_of_messages: Optional[int] = 20,
                           _=Depends(AuthService.check_user_access_token)) -> ProgressBarMessagesBetweenDatesDTO:
    """Get progress bar messages older than a given date
    """

    return ProgressBarService.get_progress_bar_messages(
        id=id, nb_of_messages=nb_of_messages, from_datetime=from_datetime)

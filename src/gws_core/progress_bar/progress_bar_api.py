# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from fastapi import Depends

from gws_core.core.utils.response_helper import ResponseHelper

from ..core_app import core_app
from ..user.auth_service import AuthService
from ..user.user_dto import UserData
from .progress_bar_service import ProgressBarService


@core_app.get("/progress-bar/{id}", tags=["Progress bar"], summary="Get a progress bar")
def get_a_progress_bar(id: str,
                       _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Retrieve a progress bar

    - **id**: the id of the progress bar
    """

    return ProgressBarService.fetch_progress_bar(id=id).to_json()


@core_app.get("/progress-bar/{id}/download", tags=["Progress bar"], summary="Get a progress bar")
def download_progress_bar(id: str,
                          _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Retrieve a progress bar

    - **id**: the id of the progress bar
    """

    logs = ProgressBarService.download_progress_bar(id=id)

    return ResponseHelper.create_file_response_from_str(logs, "messages.txt")

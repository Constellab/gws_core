# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from fastapi import Depends

from ..core_app import core_app
from ..user.auth_service import AuthService
from ..user.user_dto import UserData
from .progress_bar_service import ProgressBarService


@core_app.get("/progress-bar/{uri}", tags=["Progress bar"], summary="Get a progress bar")
async def get_a_progress_bar(uri: str,
                             _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Retrieve a progress bar

    - **uri**: the uri of the progress bar
    """

    p = ProgressBarService.fetch_progress_bar(uri=uri)
    return p.to_json()

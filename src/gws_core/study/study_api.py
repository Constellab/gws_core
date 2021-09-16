
from typing import List

from fastapi.param_functions import Depends
from gws_core.study.study_dto import StudyDto
from gws_core.study.study_service import StudyService

from ..core_app import core_app
from ..user.auth_service import AuthService
from ..user.user_dto import UserData


@core_app.get("/study", tags=["Study"])
async def read_user_me(_: UserData = Depends(AuthService.check_user_access_token)) -> List[StudyDto]:
    """
    Get the list of available studies.
    """

    return StudyService.get_available_studies()

# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from fastapi import Depends

from gws_core.core_app import core_app
from gws_core.lab.log.log import LogsBetweenDatesResponse
from gws_core.user.auth_service import AuthService
from gws_core.user.user_dto import UserData

from .process_service import ProcessService, ProcessType


@core_app.get("/process/logs/{process_type}/{id}", tags=["VEnv"],
              summary="Get the log of a process")
def get_venv_list(process_type: ProcessType,
                  id: str,
                  _: UserData = Depends(AuthService.check_user_access_token)) -> LogsBetweenDatesResponse:
    """
    Retrieve a list of running experiments.
    """

    return ProcessService.get_logs_of_process(process_type, id).to_dict()

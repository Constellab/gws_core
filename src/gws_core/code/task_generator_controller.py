# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from fastapi import Depends
from fastapi.responses import StreamingResponse

from gws_core.code.task_generator_service import TaskGeneratorService
from gws_core.core.utils.response_helper import ResponseHelper
from gws_core.core_controller import core_app
from gws_core.user.auth_service import AuthService


@core_app.post("/task-generator/from-live-task/{id}", tags=["Task generator"],
               summary="generate task code from live task")
def generate_task_code_from_live_task(id: str,
                                      _=Depends(AuthService.check_user_access_token)) -> StreamingResponse:
    code = TaskGeneratorService.generate_task_code_from_live_task_id(id)

    # create a file response
    return ResponseHelper.create_file_response_from_str(code, 'task_code.py')
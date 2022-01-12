# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from fastapi import Depends

from ..core_app import core_app
from ..user.auth_service import AuthService
from ..user.user_dto import UserData
from .task_service import TaskService


@core_app.get("/task/{id}", tags=["Task"], summary="Get a task")
async def get_a_task(id: str,
                     _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Retrieve a task

    - **type**: the type of the task (Default is `gws_core.task.task_model.Task`)
    - **id**: the id of the task
    """

    proc = TaskService.get_task_by_id(id=id)
    return proc.to_json()

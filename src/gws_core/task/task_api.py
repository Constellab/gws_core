# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Optional

from fastapi import Depends

from ..core.dto.typed_tree_dto import TypedTree
from ..core_app import core_app
from ..user.auth_service import AuthService
from ..user.user_dto import UserData
from .task_service import TaskService


@core_app.get("/task/{uri}", tags=["Task"], summary="Get a task")
async def get_a_task(uri: str,
                     _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Retrieve a task

    - **type**: the type of the task (Default is `gws_core.task.task_model.Task`)
    - **uri**: the uri of the task
    """

    proc = TaskService.get_task_by_uri(uri=uri)
    return proc.to_json()


############################# TASK TYPING ###########################
@core_app.get("/task-type", tags=["Task"], summary="Get the list of task types")
async def get_the_list_of_task_types(page: Optional[int] = 1,
                                     number_of_items_per_page: Optional[int] = 20,
                                     _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Retrieve a list of taskes. The list is paginated.

    - **page**: the page number
    - **number_of_items_per_page**: the number of items per page. Defaults to 20.
    """

    return TaskService.fetch_task_typing_list(
        page=page,
        number_of_items_per_page=number_of_items_per_page,
    ).to_json()


@core_app.get("/task-type/tree", tags=["Task"],
              summary="Get the list of task types grouped by python module")
async def get_the_list_of_task_grouped(_: UserData = Depends(AuthService.check_user_access_token)) -> List[TypedTree]:
    """
    Retrieve all the task types in TypedTree
    """

    return TaskService.fetch_task_typing_tree()


@core_app.get("/task-type/{uri}", tags=["Task"], summary="Get a task type detail")
async def get_protocol_type(uri: str,
                            _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Retrieve a task type

    - **uri**: the uri of the task type
    """

    return TaskService.get_task_typing(uri=uri).to_json(deep=True)

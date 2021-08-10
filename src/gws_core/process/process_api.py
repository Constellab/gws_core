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
from .process_service import ProcessService


@core_app.get("/process-type", tags=["Process"], summary="Get the list of process types")
async def get_the_list_of_process_types(page: Optional[int] = 1,
                                        number_of_items_per_page: Optional[int] = 20,
                                        _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Retrieve a list of processes. The list is paginated.

    - **page**: the page number
    - **number_of_items_per_page**: the number of items per page. Defaults to 20.
    """

    return ProcessService.fetch_process_type_list(
        page=page,
        number_of_items_per_page=number_of_items_per_page,
        as_json=True
    )


@core_app.get("/process-type/typedTree", tags=["Process"], summary="Get the list of process types grouped by python module")
async def get_the_list_of_process_grouped(_: UserData = Depends(AuthService.check_user_access_token)) -> List[TypedTree]:
    """
    Retrieve all the process types in TypedTree
    """

    return ProcessService.fetch_process_type_tree()


@core_app.get("/process/{type}/{uri}/progress-bar", tags=["Process"], summary="Get the progress bar of a process")
async def get_the_progress_bar_of_a_process(type: str,
                                            uri: str,
                                            _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Retrieve a process

    - **uri**: the uri of the process (Default is `gws_core.process.process.Process`)
    """

    bar = ProcessService.fetch_process_progress_bar(
        uri=uri, process_typing_name=type)
    return bar.to_json()


@core_app.get("/process/{typing_name}/{uri}", tags=["Process"], summary="Get a process")
async def get_a_process(typing_name: str,
                        uri: str,
                        _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Retrieve a process

    - **type**: the type of the process (Default is `gws_core.process.process.Process`)
    - **uri**: the uri of the process
    """

    proc = ProcessService.fetch_process(typing_name=typing_name, uri=uri)
    return proc.to_json()


@core_app.get("/process/{type}", tags=["Process"], summary="Get the list of processes")
async def get_the_list_of_processes(type: str,
                                    search_text: Optional[str] = "",
                                    experiment_uri: Optional[str] = None,
                                    page: Optional[int] = 1,
                                    number_of_items_per_page: Optional[int] = 20,
                                    _: UserData = Depends(AuthService.check_user_access_token)) -> dict:

    """
    Retrieve a list of processes. The list is paginated.

    - **type**: the type of the processes to fetch (Default is `gws_core.process.process.Process`)
    - **search_text**: text used to filter the results. The text is matched against to the `title` and the `description` using full-text search. If this parameter is given then the parameter `experiment_uri` is ignored.
    - **experiment_uri**: the uri of the experiment related to the processes. This parameter is ignored if `search_text` is given.
    - **page**: the page number
    - **number_of_items_per_page**: the number of items per page. Defaults to 20 items per page.
    """

    return ProcessService.fetch_process_list(
        typing_name=type,
        search_text=search_text,
        experiment_uri=experiment_uri,
        page=page,
        number_of_items_per_page=number_of_items_per_page,
        as_json=True
    )

# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Optional

from fastapi import Depends
from gws_core.core.classes.paginator import PaginatorDict

from ..core.dto.rendering_dto import RenderingDTO
from ..core.exception.exceptions import BadRequestException
from ..core_app import core_app
from ..user.auth_service import AuthService
from ..user.user_dto import UserData
from .model_service import ModelService


@core_app.post("/model/{typing_name}/{uri}/archive", tags=["Models"], summary="Archive a model")
async def archive_a_model(typing_name: str,
                          uri: str,
                          _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Archive a Model

    - **type**: the type of the object to archive.
    - **uri**: the uri of the object to archive
    """

    model = ModelService.archive_model(
        typing_name=typing_name,
        uri=uri
    )
    return model.to_json()


@core_app.post("/model/{typing_name}/{uri}/unarchive", tags=["Models"], summary="Unarchive a model")
async def unarchive_a_model(typing_name: str,
                            uri: str,
                            _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Unarchive a Model

    - **type**: the type of the object to archive.
    - **uri**: the uri of the object to archive
    """

    model = ModelService.unarchive_model(
        typing_name=typing_name,
        uri=uri
    )
    return model.to_json()


@core_app.get("/model/{typing_name}/{uri}/verify", tags=["Models"], summary="Verify model hash")
async def verify_a_model_hash(typing_name: str,
                              uri: str,
                              _: UserData = Depends(AuthService.check_user_access_token)) -> bool:
    """
    Verify a Model hash.

    Verify the integrity of a given object in the db. Check if this object has been altered by any unofficial mean
    (e.g. manual changes of data in db, or partial changes without taking care of its dependency chain).

    Objects' integrity is based on an algorithm that computes hashes using objects' data and their dependency trees (like in block chain) rendering any data falsification difficult to hide.

    - **type**: the type of the object to delete.
    - **uri**: the uri of the object to delete.
    - **return** `True` if the model hash is valid, `False` otherwise.
    """

    return ModelService.verify_model_hash(typing_name=typing_name, uri=uri)


@core_app.get("/model/{typing_name}/count", tags=["Models"], summary="Count the number of models")
async def count_the_number_of_models(typing_name: str,
                                     _: UserData = Depends(AuthService.check_user_access_token)) -> int:
    """
    Get the count of objects of a given type (models can be `Model` or `ViewModel`)

    - **type**: the object type
    """

    return ModelService.count_model(typing_name=typing_name)


@core_app.get("/model/{typing_name}/{uri}", tags=["Models"], summary="Get a model")
async def get_a_model(typing_name: str,
                      uri: str,
                      _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Get a Model

    - **type**: the type of the model to fetch.
    - **uri**: the uri of the model to fetch.
    """

    model = ModelService.fetch_model(typing_name=typing_name, uri=uri)
    return model.to_json()


@core_app.get("/model/{typing_name}", tags=["Models"], summary="Get the list of models")
async def get_the_list_of_models(typing_name: str,
                                 page: Optional[int] = 1,
                                 number_of_items_per_page: Optional[int] = 20,
                                 _: UserData = Depends(AuthService.check_user_access_token)) -> PaginatorDict:
    """
    Get a list of Models


    - **type**: the type of the models to fetch.
    - **search_text**: text used to filter the results. The test is matched (using full-text search) against to the `title` and the `description`.
    - **page**: the page number
    - **number_of_items_per_page**: the number of items per page. Defaults to 20 items per page.
    """

    return ModelService.fetch_list_of_models(
        typing_name=typing_name,
        page=page,
        number_of_items_per_page=number_of_items_per_page,
    ).to_json()

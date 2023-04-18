# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Optional

from fastapi import Depends
from pydantic.main import BaseModel

from gws_core.core.classes.paginator import PaginatorDict

from ..core_app import core_app
from ..user.auth_service import AuthService
from .model_service import ModelService


@core_app.post("/model/{typing_name}/{id}/archive", tags=["Models"], summary="Archive a model")
def archive_a_model(typing_name: str,
                    id: str,
                    _=Depends(AuthService.check_user_access_token)) -> dict:
    """
    Archive a Model

    - **type**: the type of the object to archive.
    - **id**: the id of the object to archive
    """

    model = ModelService.archive_model(
        typing_name=typing_name,
        id=id
    )
    return model.to_json()


@core_app.post("/model/{typing_name}/{id}/unarchive", tags=["Models"], summary="Unarchive a model")
def unarchive_a_model(typing_name: str,
                      id: str,
                      _=Depends(AuthService.check_user_access_token)) -> dict:
    """
    Unarchive a Model

    - **type**: the type of the object to archive.
    - **id**: the id of the object to archive
    """

    model = ModelService.unarchive_model(
        typing_name=typing_name,
        id=id
    )
    return model.to_json()


@core_app.get("/model/{typing_name}/{id}/verify", tags=["Models"], summary="Verify model hash")
def verify_a_model_hash(typing_name: str,
                        id: str,
                        _=Depends(AuthService.check_user_access_token)) -> bool:
    """
    Verify a Model hash.

    Verify the integrity of a given object in the db. Check if this object has been altered by any unofficial mean
    (e.g. manual changes of data in db, or partial changes without taking care of its dependency chain).

    Objects' integrity is based on an algorithm that computes hashes using objects' data and their dependency trees (like in block chain) rendering any data falsification difficult to hide.

    - **type**: the type of the object to delete.
    - **id**: the id of the object to delete.
    - **return** `True` if the model hash is valid, `False` otherwise.
    """

    return ModelService.verify_model_hash(typing_name=typing_name, id=id)


@core_app.get("/model/{typing_name}/count", tags=["Models"], summary="Count the number of models")
def count_the_number_of_models(typing_name: str,
                               _=Depends(AuthService.check_user_access_token)) -> int:
    """
    Get the count of objects of a given model type

    - **type**: the object type
    """

    return ModelService.count_model(typing_name=typing_name)


@core_app.get("/model/{typing_name}/{id}", tags=["Models"], summary="Get a model")
def get_a_model(typing_name: str,
                id: str,
                _=Depends(AuthService.check_user_access_token)) -> dict:
    """
    Get a Model

    - **type**: the type of the model to fetch.
    - **id**: the id of the model to fetch.
    """

    model = ModelService.fetch_model(typing_name=typing_name, id=id)
    return model.to_json()


@core_app.get("/model/{typing_name}", tags=["Models"], summary="Get the list of models")
def get_the_list_of_models(typing_name: str,
                           page: Optional[int] = 0,
                           number_of_items_per_page: Optional[int] = 20,
                           _=Depends(AuthService.check_user_access_token)) -> PaginatorDict:
    """
    Get a list of Models


    - **type**: the typing name of the model to fetch.
    - **page**: the page number
    - **number_of_items_per_page**: the number of items per page. Defaults to 20 items per page.
    """

    return ModelService.fetch_list_of_models(
        typing_name=typing_name,
        page=page,
        number_of_items_per_page=number_of_items_per_page,
    ).to_json()


class SearchBody(BaseModel):
    search_text: str


@core_app.post("/model/{typing_name}/search", tags=["Models"], summary="Search")
def search(typing_name: str,
           search: SearchBody,
           page: Optional[int] = 0,
           number_of_items_per_page: Optional[int] = 20,
           _=Depends(AuthService.check_user_access_token)) -> PaginatorDict:
    """
    Call search in a model


    - **typing_name**: the typing name of the model  to fetch.
    - **search_text**: text used to filter the results. The test is matched (using full-text search).
    - **page**: the page number
    - **number_of_items_per_page**: the number of items per page. Defaults to 20 items per page.
    """

    return ModelService.search(
        typing_name=typing_name,
        search_text=search.search_text,
        page=page,
        number_of_items_per_page=number_of_items_per_page,
    ).to_json()

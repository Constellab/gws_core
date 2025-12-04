from typing import Optional

from fastapi import Depends

from gws_core.core.model.model_dto import BaseModelDTO, ModelDTO, PageDTO

from ..core_controller import core_app
from ..user.authorization_service import AuthorizationService
from .model_service import ModelService


@core_app.get("/model/{typing_name}/count", tags=["Models"], summary="Count the number of models")
def count_the_number_of_models(
    typing_name: str, _=Depends(AuthorizationService.check_user_access_token)
) -> int:
    """
    Get the count of objects of a given model type

    - **type**: the object type
    """

    return ModelService.count_model(typing_name=typing_name)


class SearchBody(BaseModelDTO):
    search_text: str


@core_app.post("/model/{typing_name}/search", tags=["Models"], summary="Search")
def search(
    typing_name: str,
    search: SearchBody,
    page: Optional[int] = 0,
    number_of_items_per_page: Optional[int] = 20,
    _=Depends(AuthorizationService.check_user_access_token),
) -> PageDTO[ModelDTO]:
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
    ).to_dto()

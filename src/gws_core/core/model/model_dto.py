# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from datetime import datetime
from typing import Generic, List, TypeVar

from pydantic import BaseModel
from pydantic.generics import GenericModel

BaseModelDTOType = TypeVar('BaseModelDTOType', bound='BaseModelDTO')


class BaseModelDTO(BaseModel):
    """
    ModelDTO class.
    """

    @classmethod
    def from_json(cls, json_: dict) -> BaseModelDTOType:
        """
        Create a ModelDTO from a json.
        """
        return cls(**json_)

    @classmethod
    def from_json_list(cls, json_list: list) -> List[BaseModelDTOType]:
        """
        Create a list of ModelDTO from a list of json.
        """
        return [cls.from_json(json_) for json_ in json_list]


class ModelDTO(BaseModelDTO):
    """
    ModelDTO class.
    """
    id: str
    created_at: datetime
    last_modified_at: datetime


class PageDTO(GenericModel, Generic[BaseModelDTOType]):
    page: int
    prev_page: int
    next_page: int
    last_page: int
    total_number_of_items: int
    total_number_of_pages: int
    number_of_items_per_page: int
    is_first_page: bool
    is_last_page: bool
    total_is_approximate: bool
    objects: List[BaseModelDTOType]

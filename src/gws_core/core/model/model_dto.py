# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from datetime import datetime
from typing import Dict, Generic, List, Type, TypeVar

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from pydantic.generics import GenericModel

BaseModelDTOType = TypeVar('BaseModelDTOType', bound='BaseModelDTO')


class BaseModelDTO(BaseModel):
    """
    ModelDTO class.
    """

    def to_json_dict(self) -> dict:
        """
        Convert a ModelDTO to a json dictionary. This dict can be serialized.
        """
        return jsonable_encoder(self)

    @classmethod
    def from_json(cls: Type[BaseModelDTOType], json_: dict) -> BaseModelDTOType:
        """
        Create a ModelDTO from a json.
        """
        return cls.parse_obj(json_)

    @classmethod
    def from_json_list(cls: Type[BaseModelDTOType], json_list: list) -> List[BaseModelDTOType]:
        """
        Create a list of ModelDTO from a list of json.
        """
        return [cls.from_json(json_) for json_ in json_list]

    @classmethod
    def from_json_dict(cls: Type[BaseModelDTOType], json_dict: dict) -> Dict[str, BaseModelDTOType]:
        """
        Create a dict of ModelDTO from a dict of json.
        """
        return {key: cls.from_json(value) for key, value in json_dict.items()}


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

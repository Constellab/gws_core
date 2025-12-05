from datetime import datetime
from json import dumps
from typing import Generic, TypeVar

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

BaseModelDTOType = TypeVar("BaseModelDTOType", bound="BaseModelDTO")


class BaseModelDTO(BaseModel):
    """
    ModelDTO class.
    """

    def to_json_dict(self) -> dict:
        """
        Convert a ModelDTO to a json dictionary. This dict can be serialized.
        """
        return jsonable_encoder(self)

    def to_json_str(self) -> str:
        """
        Convert a ModelDTO to a json string.
        """
        return dumps(self.to_json_dict())

    @classmethod
    def to_json_list(
        cls: type[BaseModelDTOType], model_dto_list: list[BaseModelDTOType]
    ) -> list[dict]:
        """
        Convert a list of ModelDTO to a list of json dictionaries.
        """
        return [model_dto.to_json_dict() for model_dto in model_dto_list]

    @classmethod
    def from_json(cls: type[BaseModelDTOType], json_: dict) -> BaseModelDTOType:
        """
        Create a ModelDTO from a json.
        """
        return cls.model_validate(json_)

    @classmethod
    def from_json_str(cls: type[BaseModelDTOType], str_json: str) -> BaseModelDTOType:
        """
        Create a ModelDTO from a string json.
        """
        return cls.model_validate_json(str_json)

    @classmethod
    def from_json_list(cls: type[BaseModelDTOType], json_list: list) -> list[BaseModelDTOType]:
        """
        Create a list of ModelDTO from a list of json.
        """
        return [cls.from_json(json_) for json_ in json_list]

    @classmethod
    def from_record(cls: type[BaseModelDTOType], json_dict: dict) -> dict[str, BaseModelDTOType]:
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


class PageDTO(BaseModelDTO, Generic[BaseModelDTOType]):
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
    objects: list[BaseModelDTOType]

    @classmethod
    def empty_page(cls: type["PageDTO"]) -> "PageDTO":
        """
        Create an empty PageDTO.
        """
        return cls(
            page=1,
            prev_page=0,
            next_page=0,
            last_page=0,
            total_number_of_items=0,
            total_number_of_pages=0,
            number_of_items_per_page=0,
            is_first_page=True,
            is_last_page=True,
            total_is_approximate=False,
            objects=[],
        )

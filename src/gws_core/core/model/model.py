

import uuid
from typing import List, Type, TypeVar

from peewee import CharField, DoesNotExist
from peewee import Model as PeeweeModel

from gws_core.core.model.base_model import BaseModel
from gws_core.core.model.model_dto import BaseModelDTO, ModelDTO
from gws_core.core.utils.date_helper import DateHelper

from ..decorator.transaction import transaction
from ..exception.exceptions import NotFoundException
from ..exception.gws_exceptions import GWSException
from .db_field import DateTimeUTC

ModelType = TypeVar('ModelType', bound='BaseModel')


class Model(BaseModel, PeeweeModel):
    """
    Model class

    :property id: The id of the model (in database)
    :type id: `int`
    :property id: The unique resource identifier of the model
    :type id: `str`
    :property type: The type of the python Object (the full class name)
    :type type: `str`
    :property created_at: The creation datetime of the model
    :type created_at: `datetime`
    :property save_datetime: The last save datetime in database
    :type last_modified_at: `datetime`
    """

    id = CharField(primary_key=True, max_length=36)
    created_at = DateTimeUTC(default=DateHelper.now_utc)
    last_modified_at = DateTimeUTC(default=DateHelper.now_utc)

    # Provided at the Class level automatically by the @TypingDecorator
    _typing_name: str = None

    _json_ignore_fields: List[str] = []
    _is_saved: bool = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # If the id is not set and the __no_default__ is set, we consider that this is a new model object (not created from peewee)
        # We must use the __no_default__ because peewee does'nt always set the id directly in the __init__ (like when there are joins)
        if self.id is None and '__no_default__' not in kwargs:
            self.id = str(uuid.uuid4())
            # self.id = str(uuid.uuid4())
            self._is_saved = False
        else:
            self._is_saved = True

    def __eq__(self, other: object) -> bool:
        """
        Compares the model with another model. The models are equal if they are
        identical (same handle in memory) or have the same id in the database

        :param other: The model to compare
        :type other: `Model`
        :return: True if the models are equal
        :rtype: bool
        """

        if not isinstance(other, Model):
            return False
        return (self is other) or ((self.id is not None) and (self.id == other.id))

    def __hash__(self) -> int:
        """
        Returns the hash of the model

        :return: The hash of the model
        :rtype: int
        """

        return hash(type(self).__name__ + self.id)

    @classmethod
    def get_by_id(cls: Type[ModelType], id: str) -> ModelType | None:
        return cls.get_or_none(cls.id == id)

    @classmethod
    def get_by_ids(cls: Type[ModelType], ids: List[str]) -> List[ModelType]:
        return list(cls.select().where(cls.id.in_(ids)))

    @classmethod
    def get_by_id_and_check(cls: Type[ModelType], id: str) -> ModelType:
        """Get by ID and throw 404 error if object not found

        :param id: [description]
        :type id: str
        :return: [description]
        :rtype: str
        """
        try:
            return cls.get(cls.id == id)
        except DoesNotExist:
            raise NotFoundException(detail=GWSException.OBJECT_ID_NOT_FOUND.value,
                                    unique_code=GWSException.OBJECT_ID_NOT_FOUND.name,
                                    detail_args={"objectName": cls.classname(), "id": id})

    def is_saved(self) -> bool:
        """
        Returns True if the model is saved in db, False otherwise

        :return: True if the model is saved in db, False otherwise
        :rtype: bool
        """

        return self._is_saved

    def refresh(self: ModelType) -> ModelType:
        return self.get_by_id_and_check(self.id)

    def save(self: ModelType, *args, **kwargs) -> ModelType:
        """
        Sets the `data`
        set force_insert to True to force creation of the object
        set skip_hook to True to skip the before insert or update hook

        :param data: The input data
        :type data: dict
        :raises Exception: If the input data is not a `dict`
        """
        # set the force insert value
        # if define in params, use the value
        # otherwise true if the object was not created
        force_insert: bool = kwargs.get('force_insert') if kwargs.get(
            'force_insert') is not None else not self.is_saved()

        # if skip_hook is set to true, do not call the before insert or update
        if not kwargs.pop('skip_hook', False):
            if force_insert:
                self._before_insert()
            else:
                self._before_update()

        kwargs['force_insert'] = force_insert
        super().save(*args, **kwargs)
        self._is_saved = True

        return self

    def _before_insert(self) -> None:
        """Method to override to trigger action before the entity is inserted
        """

    def _before_update(self) -> None:
        """Method to override to trigger action before the entity is updated (not called on insert)
        """
        self.last_modified_at = DateHelper.now_utc()

    @classmethod
    @transaction()
    def save_all(cls: Type[ModelType], model_list: List[ModelType] = None) -> List[ModelType]:
        """
        Automically and safely save a list of models in the database. If an error occurs
        during the operation, the whole transactions is rolled back.

        :param model_list: List of models
        :type model_list: list
        :return: True if all the model are successfully saved, False otherwise.
        :rtype: bool
        """
        for model in model_list:
            model.save()

        return model_list

    def to_dto(self) -> BaseModelDTO:
        return ModelDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
        )

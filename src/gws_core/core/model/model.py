# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import hashlib
import json
import uuid
from typing import Any, Dict, List

from fastapi.encoders import jsonable_encoder
from peewee import (AutoField, BigAutoField, BlobField, BooleanField,
                    CharField, DoesNotExist, Field, ForeignKeyField,
                    ManyToManyField)
from peewee import Model as PeeweeModel

from gws_core.core.model.base_model import BaseModel
from gws_core.core.utils.date_helper import DateHelper

from ..decorator.json_ignore import json_ignore
from ..decorator.transaction import transaction
from ..exception.exceptions import BadRequestException, NotFoundException
from ..exception.gws_exceptions import GWSException
from ..utils.logger import Logger
from .db_field import DateTimeUTC, JSONField


@json_ignore(["hash"])
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
    :property is_archived: True if the model is archived, False otherwise. Defaults to False
    :type is_archived: `bool`
    :property data: The data of the model
    :type data: `dict`
    :property hash: The hash of the model
    :type hash: `str`
    """

    id = CharField(primary_key=True, max_length=36)
    created_at = DateTimeUTC(default=DateHelper.now_utc)
    last_modified_at = DateTimeUTC(default=DateHelper.now_utc)
    is_archived = BooleanField(default=False, index=True)
    hash = CharField(null=True)
    data: Dict[str, Any] = JSONField(null=True)

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
            if not self.data:
                self.data = {}
        else:
            self._is_saved = True

    def archive(self, archive: bool) -> 'Model':
        """
        Archive of Unarchive the model

        :param archive: True to archive, False to unarchive
        :type archive: `bool`
        :return: True if successfully done, False otherwise
        :rtype: `bool`
        """

        if self.is_archived == archive:
            return self
        self.is_archived = archive
        return self.save()

    def _create_hash_object(self):
        hash_obj = hashlib.blake2b()
        exclusion_list = (ForeignKeyField, JSONField,
                          ManyToManyField, BlobField, AutoField, BigAutoField, )

        for prop in self.property_names(Field, exclude=exclusion_list):
            try:
                if prop in ["id", "hash"]:
                    continue
                val = getattr(self, prop)
                hash_obj.update(str(val).encode())
            except Exception as err:
                Logger.error(
                    f"Erreur during the hash of the field property '{prop}'. Object: '{val}'")
                raise err

        for prop in self.property_names(JSONField):
            try:
                val = getattr(self, prop)
                hash_obj.update(json.dumps(val, sort_keys=True).encode())
            except Exception as err:
                Logger.error(
                    f"Erreur during the hash of the json field property '{prop}'. Object: '{val}'")
                raise err

        for prop in self.property_names(BlobField):
            try:
                val = getattr(self, prop)
                hash_obj.update(val)
            except Exception as err:
                Logger.error(
                    f"Erreur during the hash of the blob field property '{prop}'. Object: '{val}'")
                raise err

        for prop in self.property_names(ForeignKeyField):
            try:
                val = getattr(self, prop)
                if isinstance(val, Model):
                    if val.hash is None:
                        raise Exception(
                            f"The model '{prop}' does not have a hash. It was not saved")
                    hash_obj.update(val.hash.encode())
            except Exception as err:
                Logger.error(
                    f"Erreur during the hash of the foreign key property '{prop}'. Object: '{val}'")
                raise err

        return hash_obj

    def __compute_hash(self):
        hash_object = self._create_hash_object()
        return hash_object.hexdigest()

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
    def get_by_id(cls, id: str) -> 'Model':
        return cls.get_or_none(cls.id == id)

    @classmethod
    def get_by_ids(cls, ids: List[str]) -> List['Model']:
        return list(cls.select().where(cls.id.in_(ids)))

    @classmethod
    def get_by_id_and_check(cls, id: str) -> 'Model':
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

    def is_saved(self):
        """
        Returns True if the model is saved in db, False otherwise

        :return: True if the model is saved in db, False otherwise
        :rtype: bool
        """

        return self._is_saved

    def refresh(self) -> 'Model':
        return self.get_by_id_and_check(self.id)

    @classmethod
    def select_me(cls, *args, **kwargs):
        """
        Select objects by ensuring that the object-type is the same as the current model.
        """

        return cls.select(*args, **kwargs)

    def set_data(self, data: dict):
        """
        Sets the `data`

        :param data: The input data
        :type data: dict
        :raises Exception: If the input parameter data is not a `dict`
        """
        if isinstance(data, dict):
            self.data = data
        else:
            raise BadRequestException("The data must be a JSONable dictionary")

    def save(self, *args, **kwargs) -> 'Model':
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

        self.hash = self.__compute_hash()

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
    def save_all(cls, model_list: List['Model'] = None) -> List['Model']:
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

    def to_json(self, deep: bool = False, **kwargs) -> dict:
        """
        Returns a JSON string or dictionnary representation of the model.
        :return: The representation
        :rtype: `dict`
        """

        _json = {}

        exclusion_list = (ForeignKeyField, ManyToManyField,
                          BlobField, AutoField, BigAutoField)
        for prop in self.property_names(Field, exclude=exclusion_list):
            # if the value is json ignored
            if self._json_ignore_fields and prop in self._json_ignore_fields:
                continue
            # exclude data, it is manager after
            if prop == 'data':
                continue
            if prop.startswith("_"):
                continue  # -> private or protected property

            val = getattr(self, prop)

            _json[prop] = jsonable_encoder(val)

        # convert the data to json
        if self._json_ignore_fields and 'data' not in self._json_ignore_fields:
            _json["data"] = self.data_to_json(deep=deep, **kwargs)

        return _json

    def data_to_json(self, deep: bool = False, **kwargs) -> dict:
        """
        Returns a JSON string or dictionnary representation of the model data.
        :return: The representation
        :rtype: `dict`
        """
        _json = {}

        val = getattr(self, "data")
        _json = jsonable_encoder(val)

        return _json

    def verify_hash(self) -> bool:
        """
        Verify the current hash of the model

        :return: True if the hash is valid, False otherwise
        :rtype: `bool`
        """

        return self.hash == self.__compute_hash()

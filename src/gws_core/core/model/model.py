# ####################################################################
#
# Model
#
# ####################################################################

import hashlib
import json
import uuid
from datetime import datetime
from typing import List, Type

from fastapi.encoders import jsonable_encoder
from peewee import (AutoField, BigAutoField, BlobField, BooleanField,
                    CharField, DateTimeField, Field, ForeignKeyField,
                    ManyToManyField)
from peewee import Model as PeeweeModel
from peewee import ModelSelect
from playhouse.mysql_ext import Match

from ..db.db_manager import DbManager
from ..decorator.json_ignore import json_ignore
from ..decorator.transaction import transaction
from ..exception.exceptions import BadRequestException, NotFoundException
from ..exception.gws_exceptions import GWSException
from ..model.json_field import JSONField
from ..utils.logger import Logger
from ..utils.settings import Settings
from ..utils.utils import Utils
from .base import Base

# ####################################################################
#
# Format table name
#
# ####################################################################


def format_table_name(model: 'Model'):
    return model._table_name.lower()


@json_ignore(["id", "hash"])
class Model(Base, PeeweeModel):
    """
    Model class

    :property id: The id of the model (in database)
    :type id: `int`
    :property uri: The unique resource identifier of the model
    :type uri: `str`
    :property type: The type of the python Object (the full class name)
    :type type: `str`
    :property creation_datetime: The creation datetime of the model
    :type creation_datetime: `datetime`
    :property save_datetime: The last save datetime in database
    :type save_datetime: `datetime`
    :property is_archived: True if the model is archived, False otherwise. Defaults to False
    :type is_archived: `bool`
    :property data: The data of the model
    :type data: `dict`
    :property hash: The hash of the model
    :type hash: `str`
    """

    id = AutoField(primary_key=True)
    uri = CharField(null=True, index=True, unique=True)
    creation_datetime = DateTimeField(default=datetime.now, index=True)
    save_datetime = DateTimeField(index=True)
    is_archived = BooleanField(default=False, index=True)
    hash = CharField(null=True)
    data = JSONField(null=True)

    LAB_URI = None  # todo remove

    _data = None
    _is_removable = True
    _db_manager = DbManager
    _table_name = 'gws_model'
    # Provided at the Class level automatically by the @TypingDecorator
    _typing_name: str = None
    _json_ignore_fields: List[str] = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not Model.LAB_URI:
            Model.LAB_URI = Settings.retrieve().get_data("uri")

        if self.uri is None:
            self.uri = str(uuid.uuid4())
            if not self.data:
                self.data = {}

    # -- A --

    def add_related_model(self, relation_name: str, related_model: 'Model'):
        # ToDo : Add annotation name
        if "__relations" not in self.data:
            self.data["__relations"] = {}
        self.data["__relations"][relation_name] = {
            "uri": related_model.uri,
            "type": related_model.full_classname(),
            # "name": related_model.name
        }

    def archive(self, archive: bool) -> 'Model':
        """
        Archive of Unarchive the model

        :param archive: True to archive, False to unarchive
        :type archive: `bool`
        :return: True if sucessfully done, False otherwise
        :rtype: `bool`
        """

        if self.is_archived == archive:
            return self
        self.is_archived = archive
        cls = type(self)
        return self.save(only=[cls.is_archived])

    # -- C --

    def _create_hash_object(self):
        hash_obj = hashlib.blake2b()
        hash_obj.update(Model.LAB_URI.encode())
        exclusion_list = (ForeignKeyField, JSONField,
                          ManyToManyField, BlobField, AutoField, BigAutoField, )

        for prop in self.property_names(Field, exclude=exclusion_list):
            try:
                if prop in ["id", "hash"]:
                    continue
                val = getattr(self, prop)
                hash_obj.update(str(val).encode())
            except Exception as err:
                Logger.error(f"Erreur during the hash of the field property '{prop}'. Object: '{val}'")
                raise err

        for prop in self.property_names(JSONField):
            try:
                val = getattr(self, prop)
                hash_obj.update(json.dumps(val, sort_keys=True).encode())
            except Exception as err:
                Logger.error(f"Erreur during the hash of the json field property '{prop}'. Object: '{val}'")
                raise err

        for prop in self.property_names(BlobField):
            try:
                val = getattr(self, prop)
                hash_obj.update(val)
            except Exception as err:
                Logger.error(f"Erreur during the hash of the blob field property '{prop}'. Object: '{val}'")
                raise err

        for prop in self.property_names(ForeignKeyField):
            try:
                val = getattr(self, prop)
                if isinstance(val, Model):
                    hash_obj.update(val.hash.encode())
            except Exception as err:
                Logger.error(f"Erreur during the hash of the foreign key property '{prop}'. Object: '{val}'")
                raise err

        return hash_obj

    def __compute_hash(self):
        hash_object = self._create_hash_object()
        return hash_object.hexdigest()

    def clear_data(self, save: bool = False):
        """
        Clears the :param:`data`

        :param save: If True, save the model the :param:`data` is cleared
        :type save: bool
        """
        self.data = {}
        if save:
            self.save()

    @classmethod
    def create_table(cls, *args, **kwargs):
        """
        Create model table
        """

        if cls.table_exists():
            return
        super().create_table(*args, **kwargs)
        if cls.get_db_manager().is_mysql_engine():
            cls.get_db_manager().db.execute_sql(
                f"CREATE FULLTEXT INDEX data ON {cls.get_table_name()}(data)")

    # -- D --

    @classmethod
    def drop_table(cls, *args, **kwargs):
        """
        Drop model table
        """

        if not cls.table_exists():
            return

        super().drop_table(*args, **kwargs)

    # -- E --

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

    # -- G --

    def get_related_model(self, relation_name: str) -> 'Model':
        if ("__relations" not in self.data) or (relation_name not in self.data["__relations"]):
            raise BadRequestException(
                f"The relation {relation_name} does not exists")
        rel: dict = self.data["__relations"][relation_name]
        model_type: Type[Model] = Utils.get_model_type(rel["type"])
        return model_type.get(model_type.uri == rel["uri"])

    @classmethod
    def get_table_name(cls) -> str:
        """
        Returns the table name of this class

        :return: The table name
        :rtype: `str`
        """

        return format_table_name(cls)

    @classmethod
    def get_db_manager(cls) -> DbManager:
        """
        Returns the (current) DbManager of this model

        :return: The db manager
        :rtype: `DbManager`
        """

        return cls._db_manager

    @classmethod
    def get_by_uri(cls, uri: str) -> 'Model':
        try:
            return cls.get(cls.uri == uri)
        except:
            return None

    @classmethod
    def get_by_uri_and_check(cls, uri: str) -> 'Model':
        """Get by URI and throw 404 error if object not found

        :param uri: [description]
        :type uri: str
        :return: [description]
        :rtype: str
        """
        try:
            return cls.get(cls.uri == uri)
        except:
            raise NotFoundException(detail=GWSException.OBJECT_URI_NOT_FOUND.value,
                                    unique_code=GWSException.OBJECT_URI_NOT_FOUND.name,
                                    detail_args={"objectName": cls.classname(), "id": uri})

    # -- H --

    def hydrate_with(self, data):
        """
        Hydrate the model with data
        """

        col_names = self.property_names(Field)
        for prop in data:
            if prop == "id":
                continue
            if prop in col_names:
                setattr(self, prop, data[prop])
            else:
                self.data[prop] = data[prop]

    # -- I --

    @classmethod
    def is_sqlite3_engine(cls):
        return cls.get_db_manager().get_engine() == "sqlite3"

    @classmethod
    def is_mysql_engine(cls):
        return cls.get_db_manager().get_engine() in ["mysql", "mariadb"]

    def is_saved(self):
        """
        Returns True if the model is saved in db, False otherwise

        :return: True if the model is saved in db, False otherwise
        :rtype: bool
        """

        return bool(self.id)

    # -- N --

    # -- R --

    def refresh(self) -> None:
        """
        Refresh a model instance by re-requesting the db
        """

        cls = type(self)
        if self.id:
            db_object = cls.get_by_id(self.id)
            for prop in db_object.property_names(Field):
                db_val = getattr(db_object, prop)
                setattr(self, prop, db_val)

    @classmethod
    def select_me(cls, *args, **kwargs):
        """
        Select objects by ensuring that the object-type is the same as the current model.
        """

        return cls.select(*args, **kwargs)

    @classmethod
    def search(cls, phrase: str, in_boolean_mode: bool = False) -> ModelSelect:
        """
        Performs full-text search on the :param:`data` field

        :param phrase: The phrase to search
        :type phrase: `str`
        :param in_boolean_mode: True to search in boolean mode, False otherwise
        :type in_boolean_mode: `bool`
        """

        if in_boolean_mode:
            modifier = 'IN BOOLEAN MODE'
        else:
            modifier = None

        return cls.select().where(Match((cls.data), phrase, modifier=modifier))

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

        :param data: The input data
        :type data: dict
        :raises Exception: If the input data is not a `dict`
        """

        self.save_datetime = datetime.now()
        self.hash = self.__compute_hash()

        super().save(*args, **kwargs)

        return self

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

    # -- T --
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

    # -- U --

    @property
    def user_data(self) -> dict:
        """
        Get user data

        :return: User data
        :rtype: `dict`
        """

        if not "__user_data" in self.data:
            self.data["__user_data"] = {}
        return self.data["__user_data"]

    # -- V --

    def verify_hash(self) -> bool:
        """
        Verify the current hash of the model

        :return: True if the hash is valid, False otherwise
        :rtype: `bool`
        """

        return self.hash == self.__compute_hash()

    class Meta:
        database = DbManager.db
        table_function = format_table_name

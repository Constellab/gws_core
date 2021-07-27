# ####################################################################
#
# Model
#
# ####################################################################

import hashlib
import json
import os
import re
import shutil
from typing import List, Dict
import uuid
from datetime import datetime

from fastapi.encoders import jsonable_encoder
from peewee import (AutoField, BigAutoField, BlobField, BooleanField,
                    CharField, DateField, DateTimeField, Field,
                    ForeignKeyField, ManyToManyField)
from peewee import Model as PeeweeModel
from playhouse.mysql_ext import Match

from ..db.db_manager import DbManager
from ..db.kv_store import KVStore
from ..exception.exceptions.bad_request_exception import BadRequestException
from ..model.json_field import JSONField
from ..utils.settings import Settings
from .base import Base

# ####################################################################
#
# Format table name
#
# ####################################################################


def format_table_name(model: 'Model'):
    return model.get_table_name().lower()


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
    uri = CharField(null=True, index=True)
    type = CharField(null=True, index=True)
    creation_datetime = DateTimeField(default=datetime.now, index=True)
    save_datetime = DateTimeField(index=True)
    is_archived = BooleanField(default=False, index=True)
    hash = CharField(null=True)
    data = JSONField(null=True)

    USER_ALL = 'all'
    USER_ADMIN = 'admin'
    LAB_URI = None

    _data = None
    _kv_store: KVStore = None
    _is_singleton = False
    _is_removable = True
    _allowed_user = USER_ALL
    _db_manager = DbManager
    _table_name = 'gws_model'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not Model.LAB_URI:
            settings = Settings.retrieve()
            Model.LAB_URI = settings.get_data("uri")
        if not self.id and self._is_singleton:
            self.__init_singleton_in_place()

        if self.uri is None:
            self.uri = str(uuid.uuid4())
            if not self.data:
                self.data = {}
        # ensures that field type is allways equal to the name of the class
        if self.type is None:
            self.type = self.full_classname()
        elif self.type != self.full_classname():
            # allow object cast after ...
            pass
        self._kv_store = KVStore(self.get_kv_store_slot_path())

    # -- A --

    def add_related_model(self, relation_name: str, related_model: 'Model'):
        # ToDo : Add annotation name
        if "__relations" not in self.data:
            self.data["__relations"] = {}
        self.data["__relations"][relation_name] = {
            "uri": related_model.uri,
            "type": related_model.full_classname(),
            #"name": related_model.name
        }

    def archive(self, tf: bool) -> bool:
        """
        Archive of Unarchive the model

        :param tf: True to archive, False to unarchive
        :type tf: `bool`
        :return: True if sucessfully done, False otherwise
        :rtype: `bool`
        """

        if self.is_archived == tf:
            return True
        self.is_archived = tf
        cls = type(self)
        return self.save(only=[cls.is_archived])

    # -- B --

    @staticmethod
    def barefy(data: dict, sort_keys=False):
        if isinstance(data, dict):
            data = json.dumps(data, sort_keys=sort_keys)
        data = re.sub(
            r"\"(([^\"]*_)?uri|save_datetime|creation_datetime|hash)\"\s*\:\s*\"([^\"]*)\"", r'"\1": ""', data)
        return json.loads(data)

    # -- C --

    def __init_singleton_in_place(self):
        try:
            cls = type(self)
            model = cls.get(cls.type == self.full_classname())
        except Exception as _:
            model = None

        if model:
            # /!\ Shallow copy all properties
            for prop in model.property_names(Field):
                val = getattr(model, prop)
                setattr(self, prop, val)

    def _create_hash_object(self):
        h = hashlib.blake2b()
        h.update(Model.LAB_URI.encode())
        exclusion_list = (ForeignKeyField, JSONField,
                          ManyToManyField, BlobField, AutoField, BigAutoField, )
        for prop in self.property_names(Field, exclude=exclusion_list):
            if prop in ["id", "hash"]:
                continue
            val = getattr(self, prop)
            h.update(str(val).encode())
        for prop in self.property_names(JSONField):
            val = getattr(self, prop)
            h.update(json.dumps(val, sort_keys=True).encode())
        for prop in self.property_names(BlobField):
            val = getattr(self, prop)
            h.update(val)
        for prop in self.property_names(ForeignKeyField):
            val = getattr(self, prop)
            if isinstance(val, Model):
                h.update(val.hash.encode())
        return h

    def __compute_hash(self):
        ho = self._create_hash_object()
        return ho.hexdigest()

    def cast(self) -> 'Model':
        """
        Casts a model instance by its `type` in database.
        It is euqivalent to getting and intantiatning the real object type from db

        :return: The model
        :rtype: `Model` instance
        """

        from ..service.model_service import ModelService

        if self.type == self.full_classname():
            return self

        t = ModelService.get_model_type(self.type)
        model = t.get_by_id(self.id)
        return model

        # model = t()
        # for prop in self.property_names(Field):
        #     val = getattr(self, prop)
        #     setattr(model, prop, val)
        # return model

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
                f"CREATE FULLTEXT INDEX data ON {cls._table_name}(data)")

    # -- D --

    def delete_instance(self, *args, **kwargs):
        self.kv_store.remove()
        return super().delete_instance(*args, **kwargs)

    @classmethod
    def drop_table(cls, *args, **kwargs):
        """
        Drop model table
        """

        if not cls.table_exists():
            return

        # remove the table's path in one shot
        slot_path = cls.__get_base_kv_store_path_of_table()
        path = KVStore._create_full_dir_path(slot_path)
        if os.path.exists(path):
            shutil.rmtree(path)

        super().drop_table(*args, **kwargs)

    # -- E --

    def __eq__(self, other: 'Model') -> bool:
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
        return (self is other) or ((self.id != None) and (self.id == other.id))

    # -- F --

    @classmethod
    def fetch_type_by_id(cls, id: int) -> type:
        """
        Fecth the stored model `type` by its `id` from the database and return the corresponding python-type.
        Use the proper table even if the table name has changed by inheritance.

        :param id: The id of the model
        :type id: int
        :return: The python-type of model
        :rtype: `type`
        """

        try:
            model = cls.get(cls.id == int(id))
        except Exception as err:
            raise BadRequestException("The model is not found.") from err

        if model.full_classname() == model.type:
            return type(cls)

        from ..service.model_service import ModelService
        model_t: type = ModelService.get_model_type(model.type)
        return model_t

    # -- G --

    def get_related_model(self, relation_name: str) -> 'Model':
        if ("__relations" not in self.data) or (relation_name not in self.data["__relations"]):
            raise BadRequestException(f"The relation {relation_name} does not exists")
        rel: dict = self.data["__relations"][relation_name]
        from ..service.model_service import ModelService
        t = ModelService.get_model_type(rel["type"])
        return t.get(t.uri == rel["uri"])


    @classmethod
    def get_table_name(cls) -> str:
        """
        Returns the table name of this class

        :return: The table name
        :rtype: `str`
        """

        return cls._table_name

    @classmethod
    def get_db_manager(cls) -> DbManager:
        """
        Returns the (current) DbManager of this model

        :return: The db manager
        :rtype: `DbManager`
        """

        return cls._db_manager

    @staticmethod
    def get_brick_dir(brick_name: str):
        settings = Settings.retrieve()
        return settings.get_dependency_dir(brick_name)

    @classmethod
    def get_by_uri(cls, uri: str) -> str:
        try:
            return cls.get(cls.uri == uri)
        except Exception as _:
            return None

    @classmethod
    def __get_base_kv_store_path_of_table(cls) -> str:
        """
        Returns the base path of the KVStore

        :return: The path of the KVStore
        :rtype: str
        """

        return os.path.join(cls._table_name)

    def get_kv_store_slot_path(self) -> str:
        """
        Returns the KVStore path of the model instance

        :return: The slot path
        :rtype: str
        """

        return os.path.join(
            self.__get_base_kv_store_path_of_table(),
            self.uri
        )

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
        return cls.get_db_manager()._engine == "sqlite3"

    @classmethod
    def is_mysql_engine(cls):
        return cls.get_db_manager()._engine in ["mysql", "mariadb"]

    def is_saved(self):
        """
        Returns True if the model is saved in db, False otherwise

        :return: True if the model is saved in db, False otherwise
        :rtype: bool
        """

        return bool(self.id)

    # -- N --

    # -- K --

    @property
    def kv_store(self) -> 'KVStore':
        """
        Returns the path of the KVStore of the model

        :return: The path of the KVStore
        :rtype: str
        """

        return self._kv_store

    # -- R --

    def refresh(self):
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

        return cls.select(*args, **kwargs).where(cls.type == cls.full_classname())

    @classmethod
    def search(cls, phrase: str, in_boolean_mode: bool = False):
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

    def save(self, *args, **kwargs) -> bool:
        """
        Sets the `data`

        :param data: The input data
        :type data: dict
        :raises Exception: If the input data is not a `dict`
        """

        self.save_datetime = datetime.now()
        self.hash = self.__compute_hash()
        return super().save(*args, **kwargs)

    @classmethod
    def save_all(cls, model_list: list = None) -> bool:
        """
        Automically and safely save a list of models in the database. If an error occurs
        during the operation, the whole transactions is rolled back.

        :param model_list: List of models
        :type model_list: list
        :return: True if all the model are successfully saved, False otherwise.
        :rtype: bool
        """
        with cls.get_db_manager().db.atomic() as transaction:
            try:
                for model in model_list:
                    model.save()
            except Exception as err:
                transaction.rollback()
                raise BadRequestException(f"Error message: {err}") from err

        return True

    # -- T --

    def to_json(self, *, show_hash=False, bare: bool = False, stringify: bool = False, prettify: bool = False, jsonifiable_data_keys: list = [], **kwargs) -> (str, dict, ):
        """
        Returns a JSON string or dictionnary representation of the model.

        :param show_hash: If True, returns the hash. Defaults to False
        :type show_hash: `bool`
        :param stringify: If True, returns a JSON string. Returns a python dictionary otherwise. Defaults to False
        :type stringify: `bool`
        :param prettify: If True, indent the JSON string. Defaults to False.
        :type prettify: `bool`
        :param jsonifiable_data_keys: If is empty, `data` is fully jsonified, otherwise only specified keys are jsonified
        :type jsonifiable_data_keys: `list` of `str`
        :return: The representation
        :rtype: `dict`, `str`
        """

        _json = {}
        # jsonifiable_data_keys
        if not isinstance(jsonifiable_data_keys, list):
            jsonifiable_data_keys = []
        exclusion_list = (ForeignKeyField, ManyToManyField,
                          BlobField, AutoField, BigAutoField, )
        for prop in self.property_names(Field, exclude=exclusion_list):
            if prop in ["id"]:
                continue
            if prop.startswith("_"):
                continue  # -> private or protected property
            if prop == "data":
                _json["data"] = {}
                val = getattr(self, "data")
                if len(jsonifiable_data_keys) == 0:
                    _json["data"] = jsonable_encoder(val)
                else:
                    for k in jsonifiable_data_keys:
                        if k in val:
                            _json["data"][k] = jsonable_encoder(val[k])
            else:
                val = getattr(self, prop)
                _json[prop] = jsonable_encoder(val)
                if bare:
                    if prop == "uri" or prop == "hash" or isinstance(val, (datetime, DateTimeField, DateField)):
                        _json[prop] = ""

        if not show_hash:
            del _json["hash"]
        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
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

# Todo check
    class Meta:
        database = DbManager.db
        table_function = format_table_name

# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import inspect
import re
import uuid
import hashlib
import json
from datetime import datetime

from fastapi.encoders import jsonable_encoder
from peewee import Model as PeeweeModel
from peewee import  Field, IntegerField, FloatField, DateField, \
                    DateTimeField, CharField, BooleanField, \
                    ForeignKeyField, ManyToManyField, IPField, TextField, BlobField, \
                    AutoField, BigAutoField

from peewee import DatabaseProxy
from playhouse.sqlite_ext import RowIDField, SearchField, FTS5Model

from gws.utils import to_camel_case
from gws.logger import Error, Info
from gws.db.manager import AbstractDbManager
from gws.settings import Settings
from gws.base import Base

settings = Settings.retrieve()

# ####################################################################
#
# DbManager class
#
# ####################################################################

class DbManager(AbstractDbManager):
    db = DatabaseProxy()
    JSONField = None
    _engine = None
    _db_name = "gws"

DbManager.init("sqlite3")

# ####################################################################
#
# Misc
#
# ####################################################################

def format_table_name(model: 'Model'):
    model_name = model._table_name
    # if settings.is_prod:
    #     model_name = model_name
    # else:
    #     model_name = model_name

    return model_name.lower()

def format_fts_table_name(model: 'Model'):
    model_name = model._related_model._table_name + "_fts"
    # if settings.is_prod:
    #     model_name = model_name
    # else:
    #     model_name = model_name

    return model_name.lower()

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
    
    JSONField: callable = DbManager.JSONField

    #id = AutoField(primary_key=True)
    id = IntegerField(primary_key=True)
    uri = CharField(null=True, index=True)
    type = CharField(null=True, index=True)
    creation_datetime = DateTimeField(default=datetime.now, index=True)
    save_datetime = DateTimeField(index=True)
    is_archived = BooleanField(default=False, index=True)
    hash = CharField(null=True, index=True)
    data = JSONField(null=True, index=True)
    #document = TextField(null=True, index=True)s
    
    _kv_store: 'KVStore' = None
    _is_singleton = False
    _is_removable = True
    
    _fts_fields = {}
    _is_fts_active = True
    
    _db_manager = DbManager
    _table_name = 'gws_model'
    
    _LAB_URI = settings.get_data("uri")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if not self.id and self._is_singleton:
            try:
                cls = type(self)
                model = cls.get(cls.type == self.full_classname())
            except:
                model = None
            
            if model:
                # /!\ Shallow copy all properties (i.e. object cast) 
                # Prevent creating duplicates of processes having a representation in the db.
                for prop in model.property_names(Field):
                    val = getattr(model, prop)
                    setattr(self, prop, val) 
        
        if self.uri is None:
            self.uri = str(uuid.uuid4())

        if self.data is None:
            self.data = {} #{}

        # ensures that field type is allways equal to the name of the class
        if self.type is None:
            self.type = self.full_classname()
        elif self.type != self.full_classname():
            # allow object cast after ...
            pass
        
        from gws.store import KVStore
        self._kv_store = KVStore(self.kv_store_path)

    # -- A --
    
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
    def barefy( data: dict, sort_keys=False ):
        if isinstance(data, dict):
            data = json.dumps(data, sort_keys=sort_keys)
        data = re.sub(r"\"(([^\"]*_)?uri|save_datetime|creation_datetime|hash)\"\s*\:\s*\"([^\"]*)\"", r'"\1": ""', data)
        return json.loads(data)
    
    # -- C --
    
    def _create_hash_object(self):
        h = hashlib.blake2b()
        h.update(self._LAB_URI.encode())
        exclusion_list = (ForeignKeyField, Model.JSONField, ManyToManyField, BlobField, AutoField, BigAutoField, )
        for prop in self.property_names(Field, exclude=exclusion_list) :
            if prop in ["id", "hash"]:
                continue
            val = getattr(self, prop)            
            h.update( str(val).encode() )
         
        for prop in self.property_names(Model.JSONField):
            val = getattr(self, prop)
            h.update( json.dumps(val, sort_keys=True).encode() )
            
        for prop in self.property_names(BlobField):
            val = getattr(self, prop)
            h.update( val )
            
        for prop in self.property_names(ForeignKeyField):
            val = getattr(self, prop)
            if isinstance(val, Model):
                h.update( val.hash.encode() )

        return h
    
    def __compute_hash(self):
        ho = self._create_hash_object()
        return ho.hexdigest()

    def cast(self) -> 'Model':
        """
        Casts a model instance to its `type` in database

        :return: The model
        :rtype: `Model` instance
        """
        
        from .service.model_service import ModelService
        
        if self.type == self.full_classname():
            return self
        
        # instanciate the class and shallow copy data
        new_model_t = ModelService.get_model_type(self.type)
        model = new_model_t()
        for prop in self.property_names(Field):
            val = getattr(self, prop)
            setattr(model, prop, val)

        return model

    def clear_data(self, save: bool = False):
        """
        Clears the `data`
    
        :param save: If True, save the model the `data` is cleared
        :type save: bool
        """
        self.data = {}
        if save:
            self.save()

    @classmethod
    def create_table(cls, *args, **kwargs):
        if cls.table_exists():
            return

        if cls.fts_model():
            cls.fts_model().create_table()

        super().create_table(*args, **kwargs)

    # -- D --

    def delete_instance(self, *args, **kwargs):
        self.kv_store.remove()
        super().delete_instance(*args, **kwargs)
        
    @classmethod
    def drop_table(cls):
        if cls.fts_model():
            cls.fts_model().drop_table()
        
        from gws.store import KVStore
        KVStore.remove_all(folder=cls._table_name)
        
        super().drop_table()

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

    def fetch_typeby_id(self, id) -> 'type':
        """ 
        Fecth the model type (string) by its `id` from the database and return the corresponding python type.
        Use the proper table even if the table name has changed.

        :param id: The id of the model
        :type id: int
        :return: The model type
        :rtype: type
        """
        
        from .service.model_service import ModelService
        
        cursor = self._db_manager.db.execute_sql(f'SELECT type FROM {self._table_name} WHERE id = ?', (str(id),))
        row = cursor.fetchone()
        if len(row) == 0:
            raise Error("gws.model.Model", "fetch_typeby_id", "The model is not found.")
        typestr = row[0]
        model_t = ModelService.get_model_type(typestr)
        return model_t

    # -- G --

    @staticmethod
    def get_brick_dir(brick_name: str):
        settings = Settings.retrieve()
        return settings.get_dependency_dir(brick_name)
        
    @classmethod
    def fts_model(cls):
        if not cls.is_sqlite3_engine():
            return None
        
        if not cls._fts_fields:
            return None
        
        fts_class_name = to_camel_case(cls._table_name, capitalize_first=True) + "FTSModel"
        
        _FTSModel = type(fts_class_name, (FTSModel, ), {
            "_related_model" : cls
        })

        return _FTSModel

    @classmethod
    def get_by_uri(cls, uri: str) -> str:
        try:
            return cls.get(cls.uri == uri)
        except:
            return None

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
        return cls._db_manager._engine == "sqlite3"
    
    @classmethod
    def is_mysql_engine(cls):
        return cls._db_manager._engine in ["mysql", "mariadb"]

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
    
    @property
    def kv_store_path(self) -> str:
        """ 
        Returns the path of the KVStore of the model

        :return: The path of the KVStore
        :rtype: str
        """
        return os.path.join(self._table_name, self.uri)
    
    # -- R --
    
    def refresh(self):
        """ 
        Refresh a model using db value

        :return: The path of the KVStore
        :rtype: str
        """
        
        cls = type(self)
        if self.id:
            db_object = cls.get_by_id(cls.id)
            for prop in db_object.property_names(Field):
                db_val = getattr(db_object, prop)
                setattr(self, prop, db_val) 


    @classmethod
    def select(cls, *args, **kwargs):
        if not cls.table_exists():
            cls.create_table()
            
        return super().select(*args, **kwargs)

    @classmethod
    def select_me(cls, *args, **kwargs):
        if not cls.table_exists():
            cls.create_table()

        return cls.select( *args, **kwargs ).where(cls.type == cls.full_classname())
    
    @classmethod
    def search(cls, phrase: str):
        if cls.is_sqlite3_engine():
            _FTSModel = cls.fts_model()

            if _FTSModel is None:
                raise Error("gws.model.Model", "search", "No FTSModel model defined")

            return _FTSModel.search_bm25(
                phrase,
                weights={'score_1': 2.0, 'score_2': 1.0},
                with_score=True,
                score_alias='search_score'
            )
        elif cls.is_mysql_engine():
            return cls.select().where(cls.Match(cls.data, phrase))

    def set_data(self, data: dict):
        """ 
        Sets the `data`

        :param data: The input data
        :type data: dict
        :raises Exception: If the input parameter data is not a `dict`
        """
        if isinstance(data,dict):
            self.data = data
        else:
            raise Error("gws.model.Model", "set_data","The data must be a JSONable dictionary")

    def _save_fts_document(self):
        _FTSModel = self.fts_model()

        if _FTSModel is None:
            return True  #-> no fts fields given -> nothing to do!
        
        try:
            doc = _FTSModel.get_by_id(self.id)  
        except:
            doc = _FTSModel(rowid=self.id)

        score_1 = []
        score_2 = []

        for field in self._fts_fields:
            score = self._fts_fields[field]
            if field in self.data:
                if score > 1:
                    if isinstance(self.data[field], list):
                        score_1.append( "\n".join([str(k) for k in self.data[field]]) )
                    else:
                        score_1.append(str(self.data[field]))
                else:
                    score_2.append(str(self.data[field]))

        doc.score_1 = '\n'.join(score_1)
        doc.score_2 = '\n'.join(score_2)

        return doc.save()


    def save(self, *args, **kwargs) -> bool:
        """ 
        Sets the `data`

        :param data: The input data
        :type data: dict
        :raises Exception: If the input data is not a `dict`
        """

        if not self.table_exists():
            self.create_table()

        _FTSModel = self.fts_model()

        with self._db_manager.db.atomic() as transaction:
            try:
                if self._is_fts_active:
                    if not self._save_fts_document():
                        raise Error("gws.model.Model", "save", "Cannot save related FTS document")

                #self.kv_store.save()
                self.save_datetime = datetime.now()
                self.hash = self.__compute_hash()
                return super().save(*args, **kwargs)
            except Exception as err:
                transaction.rollback()
                raise Error("gws.model.Model", "save", f"Error message: {err}")



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
        with cls._db_manager.db.atomic() as transaction:
            try:
                #if model_list is None:
                #    return
                
                for m in model_list:
                    #if isinstance(m, cls):
                    m.save()
            except Exception as err:
                transaction.rollback()
                raise Error("gws.model.Model", "save_all", f"Error message: {err}")

        return True
    
    # -- T --

    def to_json(self, *, show_hash=False, bare: bool=False, stringify: bool=False, prettify: bool=False, jsonifiable_data_keys: list=[], **kwargs) -> (str, dict, ):
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
        
        jsonifiable_data_keys
        if not isinstance(jsonifiable_data_keys, list):
            jsonifiable_data_keys = []

        exclusion_list = (ForeignKeyField, ManyToManyField, BlobField, AutoField, BigAutoField, )

        for prop in self.property_names(Field, exclude=exclusion_list) :
            if prop in ["id"]:
                continue

            if prop.startswith("_"):
                continue  #-> private or protected property

            val = getattr(self, prop)

            if prop == "data":
                _json[prop] = {}

                if len(jsonifiable_data_keys) == 0:
                    _json[prop] = jsonable_encoder(val)
                else:
                    for k in jsonifiable_data_keys:
                        if k in val:
                            _json[prop][k] = jsonable_encoder(val[k])
            else:
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
        
        if not "_user_data_" in self.data:
            self.data["_user_data_"] = {}
            
        return self.data["_user_data_"]
    
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

# ####################################################################
#
# FTSModel class
#
# ####################################################################

class FTSModel(Base, FTS5Model):
    """
    Base class
    """

    rowid = RowIDField()
    score_1 = SearchField()
    score_2 = SearchField()
    
    _related_model = Model
    
    def get_related(self, *args, **kwargs):
        t = self._related_model
        Q = t.select( *args, **kwargs ).where(t.id == self.rowid)
        return Q[0]
    
    def save(self, *args, **kwargs) -> bool:
        if not self.table_exists():
            self.create_table()
        
        return super().save(*args, **kwargs)
    
    class Meta:
        database = DbManager.db
        table_function = format_fts_table_name
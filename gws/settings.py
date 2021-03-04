# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import tempfile
from playhouse.sqlite_ext import JSONField
from peewee import Model as PWModel
from peewee import SqliteDatabase, Proxy

database_proxy = Proxy()  # create a proxy for our db.
__cdir__ = os.path.dirname(os.path.abspath(__file__))

# app settings
class Settings(PWModel):
    data = JSONField(null = True, default={})
    
    _data = dict(
        app_dir         = __cdir__,
        app_host        = '0.0.0.0',
        app_port        = 3000,
        db_dir          = os.path.join(__cdir__, '../../'),
        db_name         = 'db.sqlite3',     # ':memory:'
        is_test         = False,
        dependencies    = {}
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if len(self.data) == 0:
            self.data = {}
            for k in self._data:
                self.data[k] = self._data[k]

    @classmethod
    def init( cls, settings_json: dict = None ):
        for k in settings_json:
            cls._data[k] = settings_json[k]

        db = SqliteDatabase( os.path.join(cls._data["db_dir"], "db_settings.sqlite3") )
        database_proxy.initialize(db)

        if not cls.table_exists():
            cls.create_table()

        try:
            settings = Settings.get_by_id(1)
            for k in cls._data:
                settings.data[k] = cls._data[k]
            
            settings.set_data("demo", False)
            settings.save()
        except:            
            settings = Settings()

            from secrets import token_bytes
            from base64 import b64encode

            #secret_key
            secret_key = b64encode(token_bytes(32)).decode()
            settings.set_data("secret_key", secret_key)

            #random token by default (security)
            token = b64encode(token_bytes(32)).decode()
            settings.set_data("token", token)

            #random central_api_key by default (security)
            if not settings.data.get("central_api_key", None):
                central_api_key = b64encode(token_bytes(32)).decode()
                settings.set_data("central_api_key", central_api_key)

            #default uri
            settings.set_data("uri", "00000000-0000-0000-0000-000000000000")

            settings.set_data("demo", False)
            settings.save()

    # -- A --

    @property
    def app(self):
        return self.data.get("app", {})

    @property
    def authors(self):
        return self.data.get("authors", None)

    def activate_fts( self, tf:bool ):
        self.data["is_fts_active"] = tf
        self.save()

    # -- B --

    # -- C --

    @property
    def smtp(self):
        return self.data.get("smtp", None)

    # -- D --

    @property
    def description(self):
        return self.app.get("description", None)
    
    @property
    def db_path(self):
        return self.build_db_path()
    
    def build_db_path(self, db_dir = None, force_production_db = False):
        if self.data["db_name"] == ':memory:':
            return self.data["db_name"]
        else:
            if not db_dir:
                db_dir = self.data["db_dir"]
              
            if self.is_test and not force_production_db:
                _db_dir = os.path.join(db_dir, "tests")
            else:
                _db_dir = db_dir
            
            if not os.path.exists(_db_dir):
                os.makedirs(_db_dir)
                    
            return os.path.join(_db_dir, self.data["db_name"])
            
    # -- G --

    def get_cwd(self) -> dict:
        return self.data["__cwd__"]

    def get_data(self, k:str, default=None) -> str:
        if k == "session_key":
            return self.data[k]
        else:
            return self.data.get(k, default)

    def get_root_dir(self) -> dict:
        d = self.get_dependency_dir("gws")
        return os.path.join(d, "../../../")

    def get_gws_workspace_dir(self) -> dict:
        rd = self.get_root_dir()
        if os.path.exists(os.path.join(rd, "./.gws/")):
            return os.path.join(rd, "./.gws/")
        else:
            return os.path.join(rd, "./gws/")

    def get_user_workspace_dir(self) -> dict:
        rd = self.get_root_dir()
        return os.path.join(rd, "./user/")

    def get_dirs(self) -> dict:
        return self.data.get("dirs",{})

    def get_dir(self, name) -> str:
        return self.data.get("dirs",{}).get(name,None)
    
    def get_file_store_dir(self) -> str:
        _folder = self.data.get("file_store_name","file_store")
        
        if self.is_test:
            _dir = os.path.join(self.data["db_dir"], "tests", _folder)
        else:
            _dir = os.path.join(self.data["db_dir"], _folder)
        
        return _dir 
    
    def get_kv_store_dir(self) -> str:
        _folder = self.data.get("kv_store_name","kv_store")
        
        if self.is_test:
            _dir = os.path.join(self.data["db_dir"], "tests", _folder)
        else:
            _dir = os.path.join(self.data["db_dir"], _folder)
        
        return _dir 

    def get_urls(self) -> dict:
        return self.data.get("urls",{})

    def get_url(self, name) -> str:
        return self.data.get("urls",{}).get(name,None)
    
    def get_log_dir(self) -> dict:
        default = os.path.join(self.get_cwd(),"logs/")
        return self.data.get("log_dir", default)
    
    def get_tmp_dir(self) -> dict:
        default = os.path.join(self.get_cwd(),"tmp/")
        return self.data.get("tmp_dir", default)
    
    def get_data_dir(self) -> dict:
        default = os.path.join(self.get_cwd(),"data/")
        return self.data.get("data_dir", default)
    
    def get_dependency_dir(self, dependency_name: str) -> str:
        return self.data["dependency_dirs"].get(dependency_name, None)

    def get_dependency_dirs(self) -> dict:
        return self.data["dependency_dirs"]
    
    def get_dependency_names(self) -> list:
        return self.data["dependencies"]
    
    def get_extern_dir(self, dependency_name: str) -> str:
        return self.data["extern_dirs"].get(dependency_name, None)

    
    def get_extern_dirs(self) -> dict:
        return self.data["extern_dirs"]

    # -- I --

    @property
    def is_test(self):
        return self.data.get("is_test", False)
    
    @property
    def is_demo(self):
        return self.data.get("is_demo", False)

    @property
    def is_debug(self):
        return self.data.get("is_debug", False)

    @property
    def is_fts_active(self):
        return self.data.get("is_fts_active", True)

    # -- N --

    @property
    def name(self):
        return self.data.get("name", None)

    # -- R --

    @classmethod
    def retrieve(cls):
        try:
            return Settings.get_by_id(1)
        except:
            raise Exception("Settings", "retrieve", "Cannot retrieve settings from the database")
   
    # -- S --

    def set_data(self, k: str, val: str):
        self.data[k] = val
        self.save()

    # -- T --

    @property
    def title(self):
        return self.app.get("title", None)
    
    # -- U --
    
    def use_prod_biota_db( self, tf: bool ):
        self.data["use_prod_biota_db"] = tf
        self.save()
        
    # -- V --

    @property
    def version(self):
        return self.data.get("version", None)
 
    class Meta:
        database = database_proxy


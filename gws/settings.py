# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from playhouse.sqlite_ext import JSONField
from peewee import Model as PWModel
from peewee import SqliteDatabase, Proxy

from gws.utils import generate_random_chars

database_proxy = Proxy()  # create a proxy for our db.
__cdir__ = os.path.dirname(os.path.abspath(__file__))

# app settings
class Settings(PWModel):
    """
    Settings class.
    
    This class represents to global settings of the application.

    :property data: The settings data
    :type data: `dict`
    """

    data = JSONField(null = True, default={})    
    _data = dict(
        app_dir         = __cdir__,
        app_host        = '0.0.0.0',
        app_port        = 3000,
        log_dir         = "/logs",
        data_dir        = "/data",
        dependencies    = {}
    )

    _table_name = "gws_settings"

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
        
        db_dir = os.path.join(cls._data["data_dir"], "settings")
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
        db = SqliteDatabase( os.path.join(db_dir, "settings.sqlite3") )
        database_proxy.initialize(db)
        
        if not cls.table_exists():
            cls.create_table()

        try:
            settings = Settings.get_by_id(1)
            for k in cls._data:
                settings.data[k] = cls._data[k]
            settings.save()
        except:            
            settings = Settings()
            #secret_key
            secret_key = generate_random_chars(128) #b64encode(token_bytes(32)).decode()
            settings.set_data("secret_key", secret_key)

            #random token by default (security)
            token = generate_random_chars(128) #b64encode(token_bytes(32)).decode()
            settings.set_data("token", token)

            #default uri
            settings.set_data("uri", "")
            settings.save()

    # -- A --

    @property
    def app(self):
        return self.data.get("app", {})

    @property
    def authors(self):
        return self.data.get("authors", None)

    # -- B --

    # -- C --

    @property
    def smtp(self):
        return self.data.get("smtp", None)

    # -- D --

    @property
    def description(self):
        return self.app.get("description", None)
    
    # -- G --

    def get_sqlite3_db_dir(self) -> str:
        db_dir = os.path.join( self.get_data_dir(), "sqlite3" )
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)

        return db_dir

    def get_maria_db_host(self) -> str:
        if self.is_dev:
            return "gws_db_dev"
        else:
            return "gws_db_prod"

    def get_cwd(self) -> dict:
        return self.data["__cwd__"]

    def get_data(self, k:str, default=None) -> str:
        if k == "session_key":
            return self.data[k]
        else:
            return self.data.get(k, default)

    def get_lab_dir(self) -> str:
        return "/lab"

    def get_log_dir(self) -> str:
        return "/logs"       

    def get_data_dir(self) -> str:
        if self.is_dev:
            return self.get_dev_data_dir()
        else:
            return self.get_prod_data_dir()

    def get_dev_data_dir(self) -> str:
        return "/dev-data"

    def get_prod_data_dir(self) -> str:
        return "/prod-data"

    def get_root_dir(self) -> str:
        return self.get_lab_dir()

    def get_gws_workspace_dir(self) -> str:
        rd = self.get_root_dir()
        if os.path.exists(os.path.join(rd, "./.gws/")):
            return os.path.join(rd, "./.gws/")
        else:
            return os.path.join(rd, "./gws/")

    def get_user_workspace_dir(self) -> str:
        rd = self.get_root_dir()
        return os.path.join(rd, "./user/")

    def get_dirs(self) -> dict:
        return self.data.get("dirs",{})

    def get_dir(self, name) -> str:
        return self.data.get("dirs",{}).get(name,None)
    
    def get_file_store_dir(self) -> str:
        if self.is_dev:
            return "/data/filestore/dev"
        else:
            return "/data/filestore/prod"
    
    def get_kv_store_dir(self) -> str:
        if self.is_dev:
            return "/data/kvstore/dev"
        else:
            return "/data/kvstore/prod"

    def get_urls(self) -> dict:
        return self.data.get("urls",{})

    def get_url(self, name) -> str:
        return self.data.get("urls",{}).get(name,None)
    
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
    def is_prod(self):
        return self.data.get("is_prod", False)

    @property
    def is_dev(self):
        return not self.is_prod

    @property
    def is_debug(self):
        return self.data.get("is_debug", False)

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
    
    # -- V --

    @property
    def version(self):
        return self.data.get("version", None)
 
    class Meta:
        database = database_proxy


# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from playhouse.sqlite_ext import JSONField
from peewee import Model as PeeweeModel
from peewee import SqliteDatabase, Proxy

from .utils import generate_random_chars

database_proxy = Proxy()  # create a proxy for our db.
__cdir__ = os.path.dirname(os.path.abspath(__file__))

# app settings
class Settings(PeeweeModel):
    """
    Settings class.
    
    This class represents to global settings of the application.

    :property data: The settings data
    :type data: `dict`
    """

    data = JSONField(null = True)
    _data = dict(
        app_dir         = __cdir__,
        app_host        = '0.0.0.0',
        app_port        = 3000,
        #log_dir         = "/logs",
        #data_dir        = "/data",
        dependencies    = {}
    )

    _table_name = "gws_settings"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.data:
            self.data = {}
            for k in self._data:
                self.data[k] = self._data[k]

    @classmethod
    def init( cls, settings_json: dict = None ):
        for k in settings_json:
            cls._data[k] = settings_json[k]
        
        settings_dir = "/settings/" #os.path.join(cls._data["data_dir"], "settings")
        if not os.path.exists(settings_dir):
            os.makedirs(settings_dir)
            
        db = SqliteDatabase(os.path.join(settings_dir, "settings.sqlite3"))
        database_proxy.initialize(db)
        
        if not cls.table_exists():
            cls.create_table()

        try:
            settings = Settings.get_by_id(1)
            for k in cls._data:
                settings.data[k] = cls._data[k]
            settings.save()
        except Exception as _:
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

    # -- D --

    @property
    def description(self):
        """ Get the app description """
        return self.app.get("description", None)
    
    # -- G --

    def get_sqlite3_db_path(self, db_name) -> str:
        db_dir = os.path.join( self.get_data_dir(), db_name, "sqlite3")
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
        db_path = os.path.join( db_dir, f"{db_name}.sqlite3" )
        return db_path

        # if self.is_prod:
        #     return self.get_sqlite3_prod_db_path(db_name)
        # else:
        #     return self.get_sqlite3_dev_db_path(db_name)

    def get_sqlite3_dev_db_path(self, db_name) -> str:
        db_dir = os.path.join( self.get_dev_data_dir(), db_name, "sqlite3")
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
        db_path = os.path.join( db_dir, f"{db_name}.sqlite3" )
        return db_path
    
    def get_sqlite3_prod_db_path(self, db_name) -> str:
        db_dir = os.path.join( self.get_prod_data_dir(), db_name, "sqlite3")
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
        db_path = os.path.join( db_dir, f"{db_name}.sqlite3" )
        return db_path

    def get_maria_db_backup_dir(self) -> str:
        return os.path.join( self.get_data_dir(), "backups" )

    def get_maria_db_host(self, db_name) -> str:
        if self.is_prod:
            return self.get_maria_prod_db_host(db_name)
        else:
            return self.get_maria_dev_db_host(db_name)

    def get_maria_prod_db_host(self, db_name) -> str:
        return f"{db_name}_prod_db"

    def get_maria_dev_db_host(self, db_name) -> str:
        return f"{db_name}_dev_db"

    def get_cwd(self) -> dict:
        return self.data["__cwd__"]

    def get_data(self, k:str, default=None) -> str:
        if k == "session_key":
            return self.data[k]
        else:
            return self.data.get(k, default)

    def get_lab_dir(self) -> str:
        """
        Get the lab directory

        :return: The lab directory
        :rtype: `str`
        """

        return "/labs"
        # if self.is_prod:
        #     return "/app/prod/lab"
        # else:
        #     return "/app/dev/lab"

    def get_log_dir(self) -> str:
        """
        Get the log directory

        :return: The log directory
        :rtype: `str`
        """

        return "/logs"
        # if self.is_prod:
        #     return "/app/prod/logs"
        # else:
        #     return "/app/dev/logs"

    def get_data_dir(self) -> str:
        """
        Get the default data directory.
        Depending on if the lab is in dev or prod mode, the appropriate directory is returned.

        :return: The default data directory
        :rtype: `str`
        """

        return "/data"
        # if self.is_prod:
        #     return self.get_prod_data_dir()
        # else:
        #     return self.get_dev_data_dir()

    def get_dev_data_dir(self) -> str:
        """
        Get the development data directory

        :return: The development data directory
        :rtype: `str`
        """

        return "/app/dev/data"

    def get_prod_data_dir(self) -> str:
        """
        Get the production data directory

        :return: The production data directory
        :rtype: `str`
        """

        return "/app/prod/data"

    def get_root_dir(self) -> str:
        """
        Get the root directory of the lab. Alias of :meth:`get_lab_dir`.

        :return: The root directory
        :rtype: `str`
        """

        return self.get_lab_dir()

    def get_gws_workspace_dir(self) -> str:
        lab_dir = self.get_lab_dir()
        if os.path.exists(os.path.join(lab_dir, "./.gws/")):
            return os.path.join(lab_dir, "./.gws/")
        else:
            return os.path.join(lab_dir, "./gws/")

    def get_user_workspace_dir(self) -> str:
        lab_dir = self.get_lab_dir()
        return os.path.join(lab_dir, "./user/")

    def get_dirs(self) -> dict:
        return self.data.get("dirs",{})

    def get_dir(self, name) -> str:
        return self.data.get("dirs",{}).get(name,None)
    
    def get_file_store_dir(self) -> str:
        return os.path.join(self.get_data_dir(), "./filestore/")
    
    def get_kv_store_base_dir(self) -> str:
        return os.path.join(self.get_data_dir(), "./kvstore/")

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

    @property
    def is_test(self):
        return self.data.get("is_test", False)

    # -- N --

    @property
    def name(self):
        return self.data.get("name", None)

    # -- R --

    @classmethod
    def retrieve(cls):
        try:
            return Settings.get_by_id(1)
        except Exception as err:
            raise Exception("Settings", "retrieve", "Cannot retrieve settings from the database") from err
   
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


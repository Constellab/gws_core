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
            if settings.data.get("central_api_key", None) is None:
                central_api_key = b64encode(token_bytes(32)).decode()
                settings.set_data("central_api_key", central_api_key)

            #no uri by default
            settings.set_data("uri", "")

            settings.set_data("demo", False)
            settings.save()

    # -- A --

    @property
    def app(self):
        return self.data.get("app", {})

    @property
    def authors(self):
        return self.data.get("authors", None)

    # -- B --

    @property
    def buttons(self) -> dict:
        sortedList = sorted(self.app["buttons"].items(),  key=lambda x: x[1].get("position",0), reverse=True)
        btns = {}
        for btn in sortedList:
            btns[ btn[0] ] = btn[1]

        return btns

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
        if self.data["db_name"] == ':memory:':
            return self.data["db_name"]
        else:
            return os.path.join(self.data["db_dir"], self.data["db_name"])

    # -- G --

    def get_cwd(self) -> dict:
        return self.data["__cwd__"]

    def get_data(self, k:str) -> str:
        if k == "session_key":
            return self.data[k]
        else:
            return self.data.get(k, None)

    def get_root_dir(self) -> dict:
        d = self.get_dependency_dir("gws")
        return os.path.join(d, "../../../")

    def get_gws_workspace_dir(self) -> dict:
        rd = self.get_root_dir()
        return os.path.join(rd, "./gws/")

    def get_user_workspace_dir(self) -> dict:
        rd = self.get_root_dir()
        return os.path.join(rd, "./user/")

    def get_dirs(self) -> dict:
        return self.data.get("dirs",{})

    def get_dir(self, name) -> str:
        return self.data.get("dirs",{}).get(name,None)

    def get_urls(self) -> dict:
        return self.data.get("urls",{})

    def get_url(self, name) -> str:
        return self.data.get("urls",{}).get(name,None)
    
    def get_log_dir(self) -> dict:
        default = os.path.join(self.get_cwd(),"logs/")
        return self.data.get("log_dir", default)

    def get_public_dir(self, name:str = None) -> dict:
        if name is None:
            return os.path.join(self.get_cwd(),"./public")
        else:
            if self.get_dependency_dir(name) is None:
                return None

            return os.path.join(self.get_dependency_dir(name),"./public")

    def get_static_dirs(self) -> dict:
        """
        Returns the absolute paths of the static directories
        :return: The absolute paths of the static directories
        :rtype: dict
        """
        statics = {}
        static_dir = self.data["app"]["statics"]
        for k in static_dir:
            if ("/"+k.strip('/')+"/").startswith("/static/"):
                statics["/"+k.strip('/')] = os.path.join(self.get_cwd(),static_dir[k])
        
        return statics

    def get_dependency_dir(self, dependency_name: str) -> str:
        return self.data["dependency_dirs"].get(dependency_name, None)

    def get_dependency_dirs(self) -> dict:
        dirs = {}
        for dep_name in self.data["dependency_dirs"]:
            dirs[dep_name] = self.data["dependency_dirs"][dep_name]
        return dirs
    
    def get_dependency_names(self) -> list:
        return self.data["dependencies"]

    # def get_dependency_paths(self) -> dict:
    #     return self.data["dependency_paths"]

    def get_template_dir(self, dependency_name: str) -> str:
        dependency_dir = self.get_dependency_dir(dependency_name)
        if dependency_dir is None:
            return None

        return os.path.join(dependency_dir, "./templates")
    
    def get_page_dir(self, dependency_name: str) -> str:
        dependency_dir = self.get_dependency_dir(dependency_name)
        if dependency_dir is None:
            return None

        return os.path.join(dependency_dir, "./web/pages")

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

    # -- V --

    @property
    def version(self):
        return self.data.get("version", None)
 
    class Meta:
        database = database_proxy


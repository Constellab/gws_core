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
    def init( cls, params: dict = None ):
        cls._data["app_dir"] = params["app_dir"]
        cls._data["db_dir"] = params["db_dir"]
        
        for k in params:
            cls._data[k] = params[k]

        db = SqliteDatabase( os.path.join(cls._data["db_dir"], "db_settings.sqlite3") )
        database_proxy.initialize(db)
        #db.connect(reuse_if_open=True)

        if not cls.table_exists():
            cls.create_table()
            
        try:
            settings = Settings.get_by_id(1)
            settings.data = cls._data
            settings.save()
        except:
            settings = Settings()
            settings.save()

    @property
    def app(self):
        return self.data.get("app", {})

    @property
    def name(self):
        return self.data.get("name", None)

    @property
    def title(self):
        return self.app.get("title", None)

    @property
    def description(self):
        return self.app.get("description", None)

    @property
    def authors(self):
        return self.data.get("authors", None)
    
    @property
    def version(self):
        return self.data.get("authors", None)

    @property
    def buttons(self) -> dict:
        sortedList = sorted(self.app["buttons"].items(),  key=lambda x: x[1].get("position",0), reverse=True)
        btns = {}
        for btn in sortedList:
            btns[ btn[0] ] = btn[1]

        return btns

    @property
    def db_path(self):
        if self.data["db_name"] == ':memory:':
            return self.data["db_name"]
        else:
            return os.path.join(self.data["db_dir"], self.data["db_name"])

    def get_cwd(self) -> dict:
        return self.data["__cwd__"]

    def get_dirs(self) -> dict:
        return self.data.get("dirs",{})

    def get_dir(self, name) -> str:
        return self.data.get("dirs",{}).get(name,None)

    def get_urls(self) -> dict:
        return self.data.get("urls",{})

    def get_url(self, name) -> str:
        return self.data.get("urls",{}).get(name,None)
    
    def get_log_dir(self) -> dict:
        # if self.data.get("is_test"):
        #     log_dir = os.path.join(tempfile.gettempdir(),"gws/logs")
        #     if not os.path.exists(log_dir):
        #         os.makedirs(log_dir)
        #     return log_dir
        # else:
        return os.path.join(self.get_cwd(),"logs/")

    def get_public_dir(self, name:str = None) -> dict:
        if name is None:
            return os.path.join(self.get_cwd(),"./public")
        else:
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
        #return os.path.join(self.get_cwd(),self.data["dependencies"][dependency_name])
        return self.data["dependencies"][dependency_name]

    def get_dependency_dirs(self) -> dict:
        dirs = {}
        for dep_name in self.data["dependencies"]:
            if not dep_name == ":external:":
                #dirs[dep_name] = os.path.join(self.get_cwd(),self.data["dependencies"][dep_name])
                dirs[dep_name] = self.data["dependencies"][dep_name]
        return dirs
    
    def get_dependency_names(self) -> list:
        names = []
        for dep_name in self.data["dependencies"]:
            if not dep_name == ":external:":
                names.append(dep_name)
        return names

    def get_dependency_paths(self) -> dict:
        return self.data["dependency_paths"]

    def get_template_dir(self, dependency_name: str) -> str:
        dependency_dir = self.get_dependency_dir(dependency_name)
        return os.path.join(dependency_dir, "./templates")

    def get_data(self, k:str) -> str:
        return self.data[k]

    def set_data(self, k: str, val: str):
        self.data[k] = val
        self.save()

    @classmethod
    def retrieve(cls):
        try:
            return Settings.get_by_id(1)
        except:
            raise Exception("Settings", "retrieve", "Cannot retrieve settings from the database")
        
    class Meta:
        database = database_proxy


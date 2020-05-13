#
# Python GWS base setting
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
#

import os
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
        app_host        = 'localhost',
        app_port        = 3000,
        static_dirs     = {},
        db_dir          = os.path.join(__cdir__, '../../'),
        db_name         = 'db.sqlite3',     # ':memory:'
        is_test         = False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if len(self.data) == 0:
            self.data = {}
            for k in self._data:
                self.data[k] = self._data[k]

    @classmethod
    def add_statics(cls, dirs: dict):
        for k in dirs:
            cls._data['static_dirs'][k] = dirs[k]

    @classmethod
    def init( cls, params: dict = None):
        cls._data["app_dir"] = params["app_dir"]
        cls._data["db_dir"] = params["db_dir"]
        
        for k in params:
            cls._data[k] = params[k]

        db = SqliteDatabase( os.path.join(cls._data["db_dir"], "db_settings.sqlite3") )
        database_proxy.initialize(db)

        db.connect(reuse_if_open=True)
        if not cls.table_exists():
            cls.create_table()
            settings = Settings()
            settings.save()

    @property
    def db_path(self):
        if self.data["db_name"] == ':memory:':
            return self.data["db_name"]
        else:
            return os.path.join(self.data["db_dir"], self.data["db_name"])

    def get_data(self, k:str) -> str:
        return self.data[k]

    def set_data(self, k: str, val: str):
        self.data[k] = val
        self.save()

    @classmethod
    def retrieve(cls):
        return Settings.get_by_id(1)

    class Meta:
        database = database_proxy


#
# Python GWS base setting
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
#

import os
from playhouse.sqlite_ext import JSONField
from peewee import Model as PWModel
from peewee import SqliteDatabase

current_dir = os.path.dirname(os.path.abspath(__file__))
db = SqliteDatabase( os.path.join(current_dir,"../db_settings.sqlite3") )
#db = SqliteDatabase( ":memory:" )  #use of in-memory database

# app settings
class Settings(PWModel):
    data = JSONField(null = True, default={})

    _data = dict(
        app_host        = 'localhost',
        app_port        = 3000,
        app_protocol    = 'http',           # http | ws
        app_dir         = current_dir,
        static_path     = os.path.join(current_dir, 'static'),
        db_dir          = os.path.join(current_dir,'../'),
        db_name         = 'db.sqlite3',     # ':memory:'
        is_test         = False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if len(self.data) == 0:
            self.data = {}
            for k in self._data:
                self.data[k] = self._data[k]

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
        database = db


db.connect(reuse_if_open=True)
if not Settings.table_exists():
    Settings.create_table()
    settings = Settings()
    settings.save()

#db.close()

from gws_core.core.db.db_config import DbConfig, DbMode
from gws_core.core.utils.settings import Settings
from peewee import DatabaseProxy

from .abstract_db_manager import AbstractDbManager


class GwsCoreDbManager(AbstractDbManager):
    db = DatabaseProxy()

    _instance: "GwsCoreDbManager" = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_config(self, mode: DbMode) -> DbConfig:
        if mode == "test":
            return Settings.get_test_db_config()
        else:
            return Settings.get_gws_core_db_config()

    def get_name(self) -> str:
        return "db"

    def get_brick_name(self) -> str:
        return Settings.get_gws_core_brick_name()

    def is_lazy_init(self):
        return False

# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core.core.db.db_config import DbConfig, DbMode
from gws_core.core.utils.settings import Settings
from peewee import DatabaseProxy

from .db_manager import AbstractDbManager

# ####################################################################
#
# DbManager class
#
# ####################################################################


class GwsCoreDbManager(AbstractDbManager):

    db = DatabaseProxy()

    @classmethod
    def get_config(cls, mode: DbMode) -> DbConfig:
        if mode == 'test':
            return Settings.get_test_db_config()
        else:
            return Settings.get_gws_core_db_config()

    @classmethod
    def get_unique_name(cls) -> str:
        return 'gws_core'

    @classmethod
    def get_brick_name(cls) -> str:
        return Settings.get_gws_core_brick_name()

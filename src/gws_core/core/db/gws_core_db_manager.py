# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from peewee import DatabaseProxy

from gws_core.core.db.db_config import DbConfig, DbMode
from gws_core.core.utils.settings import Settings

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
        settings = Settings.get_instance()
        if mode == 'test':
            return settings.get_gws_core_test_db_config()
        elif mode == 'prod':
            return settings.get_gws_core_prod_db_config()
        else:
            return settings.get_gws_core_dev_db_config()

    @classmethod
    def get_unique_name(cls) -> str:
        return 'gws_core'

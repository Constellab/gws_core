# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from peewee import DatabaseProxy

from .manager import AbstractDbManager

GWS_DB_ENGINE = "mariadb"
# GWS_DB_ENGINE="sqlite3"
# GWS_DB_ENGINE = os.getenv("LAB_DB_ENGINE", "sqlite3")

# ####################################################################
#
# DbManager class
#
# ####################################################################


class DbManager(AbstractDbManager):
    db = DatabaseProxy()

    _engine = None
    _mariadb_config = {
        "user": "gws",
        "password": "gencovery"
    }
    _db_name = "gws"


DbManager.init(engine=GWS_DB_ENGINE)

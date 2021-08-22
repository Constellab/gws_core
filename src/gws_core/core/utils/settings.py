# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from typing import Literal

from peewee import Model as PeeweeModel
from peewee import SqliteDatabase
from playhouse.sqlite_ext import JSONField

from .utils import Utils


__SETTINGS_DIR__ = "/conf/settings"
if not os.path.exists(__SETTINGS_DIR__):
    os.makedirs(__SETTINGS_DIR__)
__SETTINGS_DB__ = SqliteDatabase(
    os.path.join(__SETTINGS_DIR__, "settings.sqlite3"))

# app settings
class Settings(PeeweeModel):
    """
    Settings class.

    This class represents to global settings of the application.

    :property data: The settings data
    :type data: `dict`
    """

    data = JSONField(null=True)
    _data = dict(
        app_dir=os.path.dirname(os.path.abspath(__file__)),
        app_host='0.0.0.0',
        app_port=3000,
    )

    _table_name = "gws_settings"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.data:
            self.data = {}
            for k in self._data:
                self.data[k] = self._data[k]

    @classmethod
    def init(cls, settings_json: dict = None):
        for k in settings_json:
            cls._data[k] = settings_json[k]
        if not cls.table_exists():
            cls.create_table()
        try:
            settings = Settings.get_by_id(1)
            for k in cls._data:
                settings.data[k] = cls._data[k]
            settings.save()
        except Exception as _:
            settings = Settings()
            # secret_key
            secret_key = Utils.generate_random_chars(128)
            settings.set_data("secret_key", secret_key)
            # random token by default (security)
            token = Utils.generate_random_chars(128)
            settings.set_data("token", token)
            # default uri
            settings.set_data("uri", "")
            settings.save()

    @classmethod
    def get_prod_api_url(cls) -> str:

        if "PROD_API_URL" not in os.environ:
            return None

        return os.environ["PROD_API_URL"]

    @classmethod
    def get_lab_environment(cls) -> Literal["PROD", "LOCAL"]:
        """Return the environment where the lab run
        PROD by default but it can also be local (when running on a local machine)

        :return: [description]
        :rtype: [type]
        """

        if "LAB_ENVIRONMENT" not in os.environ:
            return "PROD"

        return os.environ["LAB_ENVIRONMENT"]

    @classmethod
    def get_virtual_host(cls) -> str:
        """Return the virtual host of the machine like tokyo.gencovery.io

        :return: [description]
        :rtype: [type]
        """

        if "VIRTUAL_HOST" not in os.environ:
            return None

        return os.environ["VIRTUAL_HOST"]

    # -- A --

    @property
    def author(self):
        return self.data.get("author","")

    # -- G --

    def get_sqlite3_db_path(self, db_name) -> str:
        db_dir = os.path.join(self.get_data_dir(), db_name, "sqlite3")
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
        db_path = os.path.join(db_dir, f"{db_name}.sqlite3")
        return db_path

    def get_maria_db_backup_dir(self) -> str:
        return os.path.join(self.get_data_dir(), "backups")

    def get_maria_db_host(self, db_name) -> str:
        if self.is_prod:
            return self.get_maria_prod_db_host(db_name)
        else:
            return self.get_maria_dev_db_host(db_name)

    def get_maria_prod_db_host(self, db_name) -> str:
        return f"{db_name}_prod_db"

    def get_maria_dev_db_host(self, db_name) -> str:
        return f"{db_name}_dev_db"

    def get_cwd(self) -> str:
        """ Returns the current working directory of the Application (i.e. the main brick directory) """
        return self.data["cwd"]

    def get_data(self, k: str, default=None) -> str:
        if k == "session_key":
            return self.data[k]
        else:
            return self.data.get(k, default)

    def get_lab_dir(self) -> str:
        """
        Get the lab directory.

        :return: The lab directory
        :rtype: `str`
        """

        return "/lab"

    def get_log_dir(self) -> str:
        """
        Get the log directory

        :return: The log directory
        :rtype: `str`
        """

        return "/logs"

    def get_data_dir(self) -> str:
        """
        Get the default data directory.
        Depending on if the lab is in dev or prod mode, the appropriate directory is returned.

        :return: The default data directory
        :rtype: `str`
        """

        return "/data"

    def get_file_store_dir(self) -> str:
        return os.path.join(self.get_data_dir(), "./filestore/")

    def get_kv_store_base_dir(self) -> str:
        return os.path.join(self.get_data_dir(), "./kvstore/")

    def get_variable(self, key) -> str:
        """ Returns a variable. Returns `None` if the variable does not exist """
        return self.data.get("variables",{}).get(key)

    def get_variables(self) -> dict:
        """ Returns the variables dict """
        return self.data.get("variables",{})

    # -- I --

    @property
    def is_prod(self) -> bool:
        return self.data.get("is_prod", False)

    @property
    def is_dev(self) -> bool:
        return not self.is_prod

    @property
    def is_debug(self) -> bool:
        return self.data.get("is_debug", False)

    @property
    def is_test(self) -> bool:
        return self.data.get("is_test", False)

    # -- N --

    @property
    def name(self):
        return self.data.get("name", None)

    # -- R --

    @classmethod
    def retrieve(cls) -> 'Settings':
        try:
            return Settings.get_by_id(1)
        except Exception as err:
            raise Exception("Settings", "retrieve",
                            "Cannot retrieve settings from the database") from err

    # -- S --

    def set_data(self, k: str, val: str):
        self.data[k] = val
        self.save()

    # -- T --

    # -- U --

    # -- V --

    @property
    def version(self):
        return self.data.get("version", None)

    class Meta:
        database = __SETTINGS_DB__

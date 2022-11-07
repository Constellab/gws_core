# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import re
import tempfile
from copy import deepcopy
from json import dump, load
from typing import Any, Dict, List, Literal, Optional, TypedDict, Union

from gws_core.core.db.db_config import DbConfig
from gws_core.impl.file.file_helper import FileHelper

from .date_helper import DateHelper
from .string_helper import StringHelper

__SETTINGS_DIR__ = "/conf/settings"
__SETTINGS_NAME__ = "settings.json"


__DEFAULT_SETTINGS__ = {
    "app_dir": os.path.dirname(os.path.abspath(__file__)),
    "app_host": '0.0.0.0',
    "app_port": 3000,
}


class ModuleInfo(TypedDict):
    path: str
    version: str
    is_brick: bool
    repo_type: Literal['app', 'git', 'pip']
    repo_commit: str
    name: str


class BrickMigrationLogHistory(TypedDict):
    version: str
    migration_date: str


class BrickMigrationLog(TypedDict):
    brick_name: str
    version: str
    last_date_check: str
    history: List[BrickMigrationLogHistory]


class Organization(TypedDict):
    id: str
    label: str
    domain: str
    photo: Optional[str]


class Settings():
    """
    Settings class.

    This class represents to global settings of the application.

    :property data: The settings data
    :type data: `dict`
    """

    data: Dict[str, Any]

    _setting_instance: 'Settings' = None

    def __init__(self, data: dict):
        self.data = data

    @classmethod
    def init(cls, settings_json: dict = None):

        settings = Settings.retrieve()

        if settings.get_data('secret_key') is None:
            # secret_key
            secret_key = StringHelper.generate_random_chars(128)
            settings.set_data("secret_key", secret_key)

        for key, value in settings_json.items():
            settings.set_data(key, value)

        settings.save()
        Settings._setting_instance = settings

    def save(self) -> bool:
        # create the parent directory
        FileHelper.create_dir_if_not_exist(__SETTINGS_DIR__)

        with open(self._get_setting_file_path(), 'w') as f:
            dump(self.data, f, sort_keys=True)

        return True

    @classmethod
    def _get_setting_file_path(cls) -> str:
        return os.path.join(__SETTINGS_DIR__, __SETTINGS_NAME__)

    @classmethod
    def _setting_file_exists(cls) -> bool:
        return FileHelper.exists_on_os(cls._get_setting_file_path())

    @classmethod
    def get_lab_prod_api_url(cls) -> str:

        if "LAB_PROD_API_URL" not in os.environ:
            return None

        return os.environ["LAB_PROD_API_URL"]

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
    def is_local_env(cls) -> bool:
        return cls.get_lab_environment() == 'LOCAL'

    @classmethod
    def get_virtual_host(cls) -> str:
        """Return the virtual host of the machine like tokyo.gencovery.io

        :return: [description]
        :rtype: [type]
        """

        if "VIRTUAL_HOST" not in os.environ:
            return None

        return os.environ["VIRTUAL_HOST"]

    @classmethod
    def get_lab_name(cls) -> str:
        """Returns the name of the lab
        """

        if "LAB_NAME" not in os.environ:
            return 'Lab'
        return os.environ["LAB_NAME"]

    @classmethod
    def get_front_version(cls) -> str:
        """Returns the front version of the lab
        """

        if "FRONT_VERSION" not in os.environ:
            return ''
        return os.environ["FRONT_VERSION"]

    @classmethod
    def get_central_api_key(cls) -> str:
        """Return the central api key

        :return: [description]
        :rtype: [type]
        """

        # specific central api key for local env
        if cls.is_local_env():
            return '123456'

        if "CENTRAL_API_KEY" not in os.environ:
            return None

        return os.environ["CENTRAL_API_KEY"]

    @classmethod
    def get_central_api_url(cls) -> str:
        """Return the central api url

        :return: [description]
        :rtype: [type]
        """

        # specific central api url for local env
        if cls.is_local_env():
            return 'http://host.docker.internal:3001'

        if "CENTRAL_API_URL" not in os.environ:
            return None

        return os.environ["CENTRAL_API_URL"]

    @classmethod
    def get_front_url(cls) -> str:
        """Return the central api url

        :return: [description]
        :rtype: [type]
        """

        # specific central api url for local env
        if cls.is_local_env():
            return 'http://localhost:4200'

        if "FRONT_URL" not in os.environ:
            return ''

        return os.environ["FRONT_URL"]

    @classmethod
    def get_global_env_dir(cls) -> str:
        return "/lab/.sys/.venv"

    def get_gws_core_prod_db_config(self) -> DbConfig:
        return {
            "host":  "gws_core_prod_db",
            "user": "gws_core",
            "password": "gencovery",
            "port": 3306,
            "db_name": "gws_core",
            "engine": "mariadb"
        }

    def get_gws_core_dev_db_config(self) -> DbConfig:
        return {
            "host":  "gws_core_dev_db",
            "user": "gws_core",
            "password": "gencovery",
            "port": 3306,
            "db_name": "gws_core",
            "engine": "mariadb"
        }

    def get_gws_core_test_db_config(self) -> DbConfig:
        return {
            "host":  "test_gws_dev_db",
            "user": "test_gws",
            "password": "gencovery",
            "port": 3306,
            "db_name": "test_gws",
            "engine": "mariadb"
        }

    # -- A --

    @property
    def author(self):
        return self.data.get("author", "")

    def get_maria_db_backup_dir(self) -> str:
        return os.path.join(self.get_data_dir(), "backups")

    def get_cwd(self) -> str:
        """ Returns the current working directory of the Application (i.e. the main brick directory) """
        return self.data["cwd"]

    def get_data(self, k: str, default=None) -> str:
        if k == "session_key":
            return self.data[k]
        else:
            return self.data.get(k, default)

    def get_brick_list(self) -> List[str]:
        return [key for key in self.data["modules"] if self.data["modules"]["is_brick"]]

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

    def get_data_dir(self, test: bool = None) -> str:
        """
        Get the default data directory.
        Depending on if the lab is in dev or prod mode, the appropriate directory is returned.

        :return: The default data directory
        :rtype: `str`
        """
        if test is None:
            test = self.is_test

        if test:
            return "/data-test"
        else:
            return "/data"

    def get_file_store_dir(self, test: bool = None) -> str:
        return os.path.join(self.get_data_dir(test=test), "./filestore/")

    def get_kv_store_base_dir(self, test: bool = None) -> str:
        return os.path.join(self.get_data_dir(test=test), "./kvstore/")

    def get_variable(self, key) -> str:
        """ Returns a variable. Returns `None` if the variable does not exist """
        value = self.data.get("variables", {}).get(key)
        return self._format_variable(value)

    def get_variables(self) -> dict:
        """ Returns the variables dict """
        variables = self.data.get("variables", {})
        for key, val in variables.items():
            variables[key] = self._format_variable(val)
        return variables

    def get_root_temp_dir(self) -> str:
        """ Return the root temp dir """
        mode = "prod" if self.is_prod else "dev"
        app = "tests" if self.is_test else "app"
        temp_dir = os.path.join(tempfile.gettempdir(), "gws", mode, app)
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        return temp_dir

    def make_temp_dir(self) -> str:
        """ Make a unique temp dir """
        return tempfile.mkdtemp(dir=self.get_root_temp_dir())

    def get_modules(self) -> Dict[str, ModuleInfo]:
        return self.data["modules"]

    def get_organization(self) -> Organization:
        return self.data.get("organization")

    def set_organization(self, organization: Organization):
        self.data["organization"] = organization

    # BRICK MIGRATION

    def get_brick_migrations_logs(self) -> Dict[str, BrickMigrationLog]:
        """Retrieve the list of all brick migrations
        """
        return self.data.get("brick_migrations", {})

    def get_brick_migration_log(self, brick_name: str) -> Union[BrickMigrationLog, None]:
        brick_migrations = self.get_brick_migrations_logs()

        return brick_migrations.get(brick_name)

    def update_brick_migration_log(self, brick_name: str, version: str) -> None:
        """Add a new brick migration log and update last migration version
        """
        brick_migrations: Dict[str, BrickMigrationLog] = self.get_brick_migrations_logs()
        brick_migration: BrickMigrationLog
        # if this is the first time the migration is executed for this brick
        if brick_name not in brick_migrations:
            brick_migration = {
                "brick_name": brick_name, "version": None, "history": [], "last_date_check": None
            }
            # add the new migration to the list of migration and save it in data
            brick_migrations[brick_name] = brick_migration

        brick_migration = brick_migrations[brick_name]
        date = DateHelper.now_utc().isoformat()

        # Update the date check
        brick_migration["last_date_check"] = date

        # update the version and history only if this is a new version
        if brick_migration["version"] != version:
            # udpate the brick version
            brick_migration["version"] = version
            # add the history
            brick_migration["history"].append({
                "version": version,
                "migration_date": date
            })
        self.data["brick_migrations"] = brick_migrations
        self.save()

    def _format_variable(self, variable: str) -> str:
        """ Format a variable """
        if not variable:
            return variable

        tabs = re.findall(r"\$\{?([A-Z_]*)\}?", variable)
        for token in tabs:
            value = os.getenv(token)
            if value:
                variable = re.sub(r"\$\{?"+token+r"\}?", value, variable)
        return variable

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

    @property
    def name(self):
        return self.data.get("name", None)

    def get_notebook_paths(self) -> str:
        """ Returns all the paths of all the brick used by the Application """
        return self.data["modules"]["notebook"]["path"]

    @classmethod
    def retrieve(cls) -> 'Settings':

        if cls._setting_instance is None:
            settings_json = None

            # try to read the settings file
            if cls._setting_file_exists():
                with open(cls._get_setting_file_path()) as f:
                    settings_json = load(f)
            # use default settings if no file exists
            else:
                settings_json = __DEFAULT_SETTINGS__

            # set the setting instance
            cls._setting_instance = Settings(settings_json)

        return cls._setting_instance

    def set_data(self, key: str, val: Any) -> None:
        self.data[key] = val

    @property
    def version(self):
        return self.data.get("version", None)

    def to_json(self) -> dict:

        # get data and remove sensitive informations
        data = deepcopy(self.data)
        del data["environment"]["variables"]
        del data["secret_key"]
        return {
            "central_api_url": self.get_central_api_url(),
            "lab_prod_api_url": self.get_lab_prod_api_url(),
            "lab_environemnt": self.get_lab_environment(),
            "virtual_host": self.get_virtual_host(),
            "cwd": self.get_cwd(),
            "lab_dir": self.get_lab_dir(),
            "log_dir": self.get_log_dir(),
            "data_dir": self.get_data_dir(),
            "file_store_dir": self.get_file_store_dir(),
            "kv_store_dir": self.get_kv_store_base_dir(),
            "data": data
        }

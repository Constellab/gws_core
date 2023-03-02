# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import re
import tempfile
from copy import deepcopy
from json import JSONDecodeError, dump, load
from typing import Any, Dict, List, Literal, Optional, Union

from gws_core.core.db.db_config import DbConfig
from gws_core.impl.file.file_helper import FileHelper
from typing_extensions import TypedDict

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
    source: str
    error: Optional[str]  # provided if the module could not be loaded


class BrickMigrationLogHistory(TypedDict):
    version: str
    migration_date: str


class BrickMigrationLog(TypedDict):
    brick_name: str
    version: str
    last_date_check: str
    history: List[BrickMigrationLogHistory]


class Space(TypedDict):
    id: str
    space: str
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

        settings = Settings.get_instance()
        settings._init_secrete_key()

        for key, value in settings_json.items():
            settings.set_data(key, value)

        settings.save()
        Settings._setting_instance = settings

    def save(self) -> bool:
        # create the parent directory
        FileHelper.create_dir_if_not_exist(__SETTINGS_DIR__)

        with open(self._get_setting_file_path(), 'w', encoding='UTF-8') as f:
            dump(self.data, f, sort_keys=True)

        return True

    def _init_secrete_key(self):
        # if a secrete key is set in the environment variable, use it
        secrete_key_env = os.environ.get("SECRET_KEY")
        if secrete_key_env:
            self.set_data("secret_key", secrete_key_env)

        # if no secrete key is set, generate one if not already set
        if self.get_data('secret_key') is None:
            # secret_key
            secret_key = StringHelper.generate_random_chars(128)
            self.set_data("secret_key", secret_key)

    @classmethod
    def _get_setting_file_path(cls) -> str:
        return os.path.join(__SETTINGS_DIR__, __SETTINGS_NAME__)

    @classmethod
    def _setting_file_exists(cls) -> bool:
        return FileHelper.exists_on_os(cls._get_setting_file_path())

    @classmethod
    def get_lab_prod_api_url(cls) -> str:
        return os.environ.get("LAB_PROD_API_URL")

    @classmethod
    def get_lab_dev_api_url(cls) -> str:
        return os.environ.get("LAB_DEV_API_URL")

    @classmethod
    def get_gws_core_db_password(cls) -> str:
        return os.environ.get("GWS_CORE_DB_PASSWORD")

    @classmethod
    def get_lab_environment(cls) -> Literal["PROD", "LOCAL"]:
        """Return the environment where the lab run
        PROD by default but it can also be local (when running on a local machine)

        :return: [description]
        :rtype: [type]
        """
        return os.environ.get("LAB_ENVIRONMENT", 'PROD')

    @classmethod
    def is_local_env(cls) -> bool:
        return cls.get_lab_environment() == 'LOCAL'

    @classmethod
    def get_virtual_host(cls) -> str:
        """Return the virtual host of the machine like tokyo.gencovery.io

        :return: [description]
        :rtype: [type]
        """
        return os.environ.get("VIRTUAL_HOST")

    @classmethod
    def get_lab_id(cls) -> str:
        """Returns the name of the lab
        """

        # specific lab id for local env
        if cls.is_local_env() and not os.environ.get("LAB_ID"):
            return '1'

        return os.environ.get("LAB_ID")

    @classmethod
    def get_lab_name(cls) -> str:
        """Returns the name of the lab
        """
        return os.environ.get("LAB_NAME", 'Lab')

    @classmethod
    def get_front_version(cls) -> str:
        """Returns the front version of the lab
        """
        return os.environ.get("FRONT_VERSION", '')

    @classmethod
    def get_central_api_key(cls) -> str:
        """Return the central api key

        :return: [description]
        :rtype: [type]
        """

        # specific central api key for local env
        if cls.is_local_env() and not os.environ.get("CENTRAL_API_KEY"):
            return '123456'

        return os.environ.get("CENTRAL_API_KEY")

    @classmethod
    def get_central_api_url(cls) -> str:
        """Return the central api url

        :return: [description]
        :rtype: [type]
        """

        # specific central api url for local env
        if cls.is_local_env() and not os.environ.get("CENTRAL_API_URL"):
            return 'http://host.docker.internal:3001'

        return os.environ.get("CENTRAL_API_URL")

    @classmethod
    def get_front_url(cls) -> str:
        """Return the central api url

        :return: [description]
        :rtype: [type]
        """

        # specific central api url for local env
        if cls.is_local_env() and not os.environ.get("FRONT_URL"):
            return 'http://localhost:4200'

        return os.environ.get("FRONT_URL", '')

    @classmethod
    def get_lab_folder(cls) -> str:
        return '/lab'

    @classmethod
    def get_user_bricks_folder(cls) -> str:
        return os.path.join(cls.get_lab_folder(), 'user', 'bricks')

    @classmethod
    def _get_system_folder(cls) -> str:
        return os.path.join(cls.get_lab_folder(), '.sys')

    @classmethod
    def get_global_env_dir(cls) -> str:
        return os.path.join(cls._get_system_folder(), ".env")

    def get_gws_core_prod_db_config(self) -> DbConfig:
        return {
            "host":  "gws_core_prod_db",
            "user": "gws_core",
            "password": self.get_gws_core_db_password(),
            "port": 3306,
            "db_name": "gws_core",
            "engine": "mariadb"
        }

    def get_gws_core_dev_db_config(self) -> DbConfig:
        return {
            "host":  "gws_core_dev_db",
            "user": "gws_core",
            "password": self.get_gws_core_db_password(),
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

    def get_log_dir(self) -> str:
        """
        Get the log directory

        :return: The log directory
        :rtype: `str`
        """
        if self.is_test:
            return "/logs-test"
        else:
            return "/logs"

    def get_data_dir(self) -> str:
        """
        Get the default data directory.
        Depending on if the lab is in dev or prod mode, the appropriate directory is returned.

        :return: The default data directory
        :rtype: `str`
        """
        if self.is_test:
            return "/data-test"
        else:
            return "/data"

    def get_brick_data_main_dir(self) -> str:
        """
        Get the main data director for the brick.
        It contains folder for each brick containing data of the brick.

        :param brick_name: The name of the brick
        :type brick_name: `str`
        :return: The brick data directory
        :rtype: `str`
        """
        if self.is_test:
            return os.path.join(self._get_system_folder(), 'brick-data-test')
        else:
            return os.path.join(self._get_system_folder(), 'brick-data')

    def get_brick_data_dir(self, brick_name: str) -> str:
        """
        Get the data directory of a brick.
        It contains the data downloaded for a brick.

        :param brick_name: The name of the brick
        :type brick_name: `str`
        :return: The brick data directory
        :rtype: `str`
        """
        return os.path.join(self.get_brick_data_main_dir(), brick_name)

    def get_file_store_dir(self) -> str:
        return os.path.join(self.get_data_dir(), "filestore")

    def get_kv_store_base_dir(self) -> str:
        return os.path.join(self.get_data_dir(), "kvstore")

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

        return os.path.join(self._get_system_folder(), 'tmp')

    def make_temp_dir(self) -> str:
        """ Make a unique temp dir """
        dir = self.get_root_temp_dir()

        if not os.path.exists(dir):
            os.makedirs(dir)
        return tempfile.mkdtemp(dir=dir)

    def get_modules(self) -> Dict[str, ModuleInfo]:
        return self.data["modules"]

    def get_space(self) -> Space:
        return self.data.get("space")

    def set_space(self, space: Space):
        self.data["space"] = space

    def get_lab_api_url(self) -> str:
        return self.get_lab_prod_api_url() if self.is_prod else self.get_lab_dev_api_url()

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
    def get_instance(cls) -> 'Settings':
        if cls._setting_instance is None:
            settings_json = None

            # try to read the settings file
            if cls._setting_file_exists():
                with open(cls._get_setting_file_path(), encoding='UTF-8') as f:
                    try:
                        settings_json = load(f)
                    except JSONDecodeError as err:
                        print(
                            f"Error while reading settings file at '{cls._get_setting_file_path()}'. Please check the syntax of the file. Here is the file content")
                        print(f.read())
                        raise err
            # use default settings if no file exists
            else:
                settings_json = __DEFAULT_SETTINGS__

            # set the setting instance
            cls._setting_instance = Settings(settings_json)

        return cls._setting_instance

    @classmethod
    def retrieve(cls) -> 'Settings':
        print("[SETTINGS] Method 'retrieve' deprecated, please use 'get_instance'")
        return cls.get_instance()

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
            "lab_id": self.get_lab_id(),
            "lab_name": self.get_lab_name(),
            "central_api_url": self.get_central_api_url(),
            "lab_prod_api_url": self.get_lab_prod_api_url(),
            "lab_dev_api_url": self.get_lab_dev_api_url(),
            "lab_environemnt": self.get_lab_environment(),
            "virtual_host": self.get_virtual_host(),
            "cwd": self.get_cwd(),
            "log_dir": self.get_log_dir(),
            "data_dir": self.get_data_dir(),
            "file_store_dir": self.get_file_store_dir(),
            "kv_store_dir": self.get_kv_store_base_dir(),
            "data": data
        }

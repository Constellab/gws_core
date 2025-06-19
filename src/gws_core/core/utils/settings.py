

import os
import re
import tempfile
from copy import deepcopy
from json import JSONDecodeError, dump, load
from typing import Any, Dict, List, Optional, Union, cast

from gws_core.brick.brick_dto import BrickInfo
from gws_core.core.db.db_config import DbConfig
from gws_core.impl.file.file_helper import FileHelper
from gws_core.lab.system_dto import (BrickMigrationLog, LabEnvironment,
                                     ModuleInfo, PipPackage, SettingsDTO)
from gws_core.user.user_dto import SpaceDict

from .date_helper import DateHelper
from .string_helper import StringHelper

# TODO RENAME FILE
__SETTINGS_DIR__ = "/conf/settings"
__SETTINGS_NAME__ = "settings.json"


__DEFAULT_SETTINGS__ = {
    "app_dir": os.path.dirname(os.path.abspath(__file__)),
    "app_host": '0.0.0.0',
    "app_port": 3000,
}


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
    def init(cls) -> 'Settings':

        settings = Settings.get_instance()
        settings._init_secrete_key()

        Settings._setting_instance = settings

        settings.data['modules'] = {}
        settings.data['bricks'] = {}

        return settings

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
    def is_prod_mode(cls) -> bool:
        return os.environ.get("LAB_MODE", "dev") == "prod"

    @classmethod
    def is_dev_mode(cls) -> bool:
        return not cls.is_prod_mode()

    @classmethod
    def get_lab_prod_api_url(cls) -> str:
        return os.environ.get("LAB_PROD_API_URL")

    @classmethod
    def get_lab_dev_api_url(cls) -> str:
        return os.environ.get("LAB_DEV_API_URL")

    @classmethod
    def get_lab_api_url(cls) -> str:
        return cls.get_lab_prod_api_url() if cls.is_prod_mode() else cls.get_lab_dev_api_url()

    @classmethod
    def core_api_route_path(cls) -> str:
        return "core-api"

    @classmethod
    def space_api_route_path(cls) -> str:
        return "space-api"

    @classmethod
    def external_lab_api_route_path(cls) -> str:
        return "external-lab-api"

    @classmethod
    def s3_server_api_route_path(cls) -> str:
        return "s3-server"

    @classmethod
    def prod_api_sub_domain(cls) -> str:
        return "glab"

    @classmethod
    def dev_api_sub_domain(cls) -> str:
        return "glab-dev"

    @classmethod
    def get_lab_environment(cls) -> LabEnvironment:
        """Return the environment where the lab run
        ON_CLOUD : the lab is running on the cloud
        DESKTOP : the lab is running on a desktop
        LOCAL : the lab is running locally (for development purpose)

        :return: [description]
        :rtype: [type]
        """
        return cast(LabEnvironment, os.environ.get("LAB_ENVIRONMENT", 'ON_CLOUD'))

    @classmethod
    def get_community_api_url(cls) -> str:
        if cls.is_local_env():
            return 'http://host.docker.internal:3333'
        return os.getenv("COMMUNITY_API_URL")

    @classmethod
    def get_community_front_url(cls) -> str:
        return os.getenv("COMMUNITY_FRONT_URL")

    @classmethod
    def is_local_env(cls) -> bool:
        return cls.get_lab_environment() == 'LOCAL'

    @classmethod
    def is_cloud_env(cls) -> bool:
        return cls.get_lab_environment() == 'ON_CLOUD'

    @classmethod
    def get_virtual_host(cls) -> str:
        """Return the virtual host of the machine like tokyo.gencovery.io

        :return: [description]
        :rtype: [type]
        """
        return os.environ.get("VIRTUAL_HOST")

    @classmethod
    def gpu_is_available(cls) -> bool:
        """return true if the gpu is available
        """
        return os.environ.get("GPU", "") != ""

    @classmethod
    def get_gws_core_brick_name(cls) -> str:
        return 'gws_core'

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
    def get_space_api_key(cls) -> str:
        """Return the space api key

        :return: [description]
        :rtype: [type]
        """

        # specific space api key for local env
        if cls.is_local_env() and not os.environ.get("SPACE_API_KEY"):
            return '123456'

        # TODO remove CENTRAL_API_KEY once all lab manager are updated to v1.9.0
        return os.environ.get("SPACE_API_KEY") or os.environ.get("CENTRAL_API_KEY")

    @classmethod
    def get_space_api_url(cls) -> str:
        """Return the space api url

        :return: [description]
        :rtype: [type]
        """

        # specific space api url for local env
        if cls.is_local_env() and not os.environ.get("SPACE_API_URL"):
            return 'http://host.docker.internal:3001'

        # TODO remove CENTRAL_API_URL once all lab manager are updated to v1.9.0
        return os.environ.get("SPACE_API_URL") or os.environ.get("CENTRAL_API_URL")

    @classmethod
    def get_front_url(cls) -> str:

        if cls.is_local_env() and not os.environ.get("FRONT_URL"):
            return 'http://localhost:4200'

        return os.environ.get("FRONT_URL", '')

    @classmethod
    def get_open_ai_api_key(cls) -> str:
        """Return the open ai api key

        :return: [description]
        :rtype: [type]
        """
        return os.environ.get("OPENAI_API_KEY")

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
    def get_main_app_folder(cls) -> str:
        return os.path.join(cls._get_system_folder(), 'app')

    @classmethod
    def get_global_env_dir(cls) -> str:
        return os.path.join(cls._get_system_folder(), ".env")

    @classmethod
    def get_sys_bricks_folder(cls) -> str:
        return os.path.join(cls._get_system_folder(), "bricks")

    @classmethod
    def get_gws_core_db_config(cls) -> DbConfig:
        return {
            "host":  os.environ.get("GWS_CORE_DB_HOST"),
            "user": os.environ.get("GWS_CORE_DB_USER"),
            "password": os.environ.get("GWS_CORE_DB_PASSWORD"),
            "port": int(os.environ.get("GWS_CORE_DB_PORT")),
            "db_name": os.environ.get("GWS_CORE_DB_NAME"),
            "engine": "mariadb"
        }

    @classmethod
    def get_test_db_config(cls) -> DbConfig:
        return {
            "host":  os.environ.get("GWS_TEST_DB_HOST"),
            "user": os.environ.get("GWS_TEST_DB_USER"),
            "password": os.environ.get("GWS_TEST_DB_PASSWORD"),
            "port": int(os.environ.get("GWS_TEST_DB_PORT")),
            "db_name": os.environ.get("GWS_TEST_DB_NAME"),
            "engine": "mariadb"
        }

    @classmethod
    def get_root_temp_dir(cls) -> str:
        """ Return the root temp dir """

        return os.path.join(cls._get_system_folder(), 'tmp')

    @classmethod
    def make_temp_dir(cls) -> str:
        """ Make a unique temp dir """
        dir_ = cls.get_root_temp_dir()

        if not os.path.exists(dir_):
            os.makedirs(dir_)
        return tempfile.mkdtemp(dir=dir_)

    @classmethod
    def build_log_dir(cls, is_test: bool) -> str:
        """ Return the log dir """
        if is_test:
            return "/logs-test"
        else:
            return "/logs"

    ##### APPS ####
    @classmethod
    def get_app_ports(cls) -> List[int]:
        """Returns available port for streamlit addtional app (running in virtual env)
        """
        if os.environ.get("APP_PORTS"):
            # if the APP_PORTS is set, use it as the first port
            return [int(port) for port in os.environ.get("APP_PORTS").split(",")]
        # TODO remove once all lab manager are updated to v1.21.0
        elif os.environ.get("STREAMLIT_APP_SERVER_PORT") and os.environ.get("STREAMLIT_APP_ADDITIONAL_PORTS"):
            main_port = int(os.environ.get("STREAMLIT_APP_SERVER_PORT"))
            other_ports = [int(port) for port in os.environ.get(
                "STREAMLIT_APP_ADDITIONAL_PORTS").split(",")]
            return [main_port] + other_ports
        else:
            # default ports
            return [8501, 8502, 8503]

    @classmethod
    def get_app_hosts(cls) -> List[str]:
        """Returns available port for streamlit addtional app (running in virtual env)
        """
        if os.environ.get("APP_HOSTS"):
            # if the APP_HOSTS is set, use it as the first host
            return [host for host in os.environ.get("APP_HOSTS").split(",")]
        # TODO remove once all lab manager are updated to v1.21.0
        elif os.environ.get("STREAMLIT_APP_SERVER_HOST") and os.environ.get("STREAMLIT_APP_ADDITIONAL_HOSTS"):
            main_host = os.environ.get("STREAMLIT_APP_SERVER_HOST")
            other_hosts = [host for host in os.environ.get("STREAMLIT_APP_ADDITIONAL_HOSTS").split(",")]
            return [main_host] + other_hosts
        else:
            # default hosts
            return ["dashboard1", "dashboard2", "dashboard3"]

    def get_gws_core_db_name(self) -> str:
        return 'gws_core'

    def get_maria_db_backup_dir(self) -> str:
        return os.path.join(self.get_data_dir(), "backups")

    def get_main_settings_file_path(self) -> str:
        return self.data["main_settings_file_path"]

    def set_main_settings_file_path(self, main_settings_file_path: str):
        self.data["main_settings_file_path"] = main_settings_file_path

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
        return self.build_log_dir(self.is_test)

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

    def get_modules(self) -> Dict[str, ModuleInfo]:
        return self.data.get("modules", {})

    def add_module(self, module_info: ModuleInfo) -> None:
        if 'modules' not in self.data:
            self.data['modules'] = {}
        self.data["modules"][module_info["name"]] = module_info

    def get_bricks(self) -> Dict[str, BrickInfo]:
        return BrickInfo.from_record(self.data.get("bricks", {}))

    def get_brick(self, brick_name: str) -> Union[BrickInfo, None]:
        return self.get_bricks().get(brick_name)

    def add_brick(self, brick_info: BrickInfo) -> None:
        if 'bricks' not in self.data:
            self.data['bricks'] = {}
        self.data["bricks"][brick_info.name] = brick_info.to_json_dict()

    def get_space(self) -> SpaceDict:
        return self.data.get("space")

    def set_space(self, space: SpaceDict):
        self.data["space"] = space

    def set_pip_freeze(self, pip_freeze: List[str]):
        self.data["pip_freeze"] = pip_freeze

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
        brick_migrations: Dict[str,
                               BrickMigrationLog] = self.get_brick_migrations_logs()
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

    def set_variable(self, key: str, value: str) -> None:
        """ Set a variable """
        self.data.setdefault("variables", {})[key] = value

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

    def is_local_dev_env(self) -> bool:
        """True when lab is running locally in dev mode

        :return: _description_
        :rtype: bool
        """
        return self.is_local_env() and self.is_dev_mode()

    def is_desktop_lab(self) -> bool:
        """True when lab is running on a desktop in prod mode

        :return: _description_
        :rtype: bool
        """
        return self.is_local_env() and self.is_prod_mode()

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
                with open(cls._get_setting_file_path(), encoding='UTF-8') as file:
                    try:
                        settings_json = load(file)
                    except JSONDecodeError as err:
                        print(
                            f"Error while reading settings file at '{cls._get_setting_file_path()}'. Please check the syntax of the file. Here is the file content")
                        print(file.read())
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

    def to_dto(self) -> SettingsDTO:

        # get data and remove sensitive informations
        data = deepcopy(self.data)
        del data["secret_key"]
        return SettingsDTO(
            lab_id=self.get_lab_id(),
            lab_name=self.get_lab_name(),
            space_api_url=self.get_space_api_url(),
            lab_prod_api_url=self.get_lab_prod_api_url(),
            lab_dev_api_url=self.get_lab_dev_api_url(),
            lab_environment=self.get_lab_environment(),
            virtual_host=self.get_virtual_host(),
            main_settings_file_path=self.get_main_settings_file_path(),
            log_dir=self.get_log_dir(),
            data_dir=self.get_data_dir(),
            file_store_dir=self.get_file_store_dir(),
            kv_store_dir=self.get_kv_store_base_dir(),
            data=data
        )

    ############################ PIP PACKAGES ############################
    def get_all_pip_packages(self) -> List[PipPackage]:
        pip_freeze = self.data.get("pip_freeze", [])
        pip_packages: List[PipPackage] = []
        for pip_package in pip_freeze:
            if not pip_package or "==" not in pip_package:
                continue

            pip_packages.append(PipPackage(
                name=pip_package.split("==")[0],
                version=pip_package.split("==")[1]
            ))

        return pip_packages

    def get_pip_packages(self, names: List[str]) -> List[PipPackage]:
        pip_packages = self.get_all_pip_packages()
        return [pip_package for pip_package in pip_packages if pip_package.name in names]

    def get_pip_package(self, name: str) -> Optional[PipPackage]:
        pip_packages = self.get_all_pip_packages()
        for pip_package in pip_packages:
            if pip_package.name == name:
                return pip_package
        return None

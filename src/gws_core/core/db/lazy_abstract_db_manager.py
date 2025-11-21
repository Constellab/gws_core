
from abc import abstractmethod
from typing import cast

from gws_core.core.db.abstract_db_manager import AbstractDbManager
from gws_core.core.db.db_config import DbConfig, DbMode
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.credentials.credentials_type import CredentialsDataBasic
from gws_core.docker.docker_service import DockerService
from gws_core.user.current_user_service import AuthenticateUser
from typing_extensions import final


class LazyAbstractDbManager(AbstractDbManager):
    """
    Abstract Database Manager that automatically handles Docker container startup logic.

    Subclasses only need to define:
    - get_name: Name of the DB for this brick
    - get_brick_name: Name of the brick

    Everything else (host, database name, port, credentials, network configuration)
    is handled automatically.

    Example:
        class MyBrickDbManager(LazyAbstractDbManager):
            db = DatabaseProxy()

            _instance: Optional['MyBrickDbManager'] = None

            @classmethod
            def get_instance(cls) -> 'MyBrickDbManager':
                if cls._instance is None:
                    cls._instance = cls()
                return cls._instance

            def get_name(self) -> str:
                return 'db'

            def get_brick_name(self) -> str:
                return 'my_brick'
    """

    # Default configuration
    PORT = 3306

    _config: DbConfig = None

    def init(self, mode: DbMode):
        """Initialize the database by starting the Docker container first"""
        self._start_docker_compose(mode)
        return super().init(mode)

    def _start_docker_compose(self, mode: DbMode):
        """Start the Docker container for the database"""
        if mode == 'test':
            return
        docker_service = DockerService()

        try:
            brick_name = self.get_brick_name()

            Logger.info(f'Starting {self.get_unique_name()} database container')
            with AuthenticateUser.system_user():
                docker_service.register_sqldb_compose(
                    brick_name=brick_name,
                    unique_name=self.get_name(),
                    database_name=self.get_unique_name(),
                    description=f'{brick_name} brick database in {mode} mode',
                )
                Logger.info(f'{self.get_unique_name()} database container started')

        except Exception as err:
            # If the lab manager failed to start the docker, we try to get the credentials to connect
            Logger.info(f"Cannot start the {self.get_brick_name()} db compose, skipping startup.")

            if not Settings.is_local_env():
                Logger.log_exception_stack_trace(err)

    def get_config(self, mode: DbMode) -> DbConfig:
        """Get database configuration with credentials from Docker service"""
        if mode == 'test':
            return Settings.get_test_db_config()

        if self._config is None:
            docker_service = DockerService()
            credentials = docker_service.get_basic_credentials(
                brick_name=self.get_brick_name(),
                unique_name=self.get_name(),
            )
            if not credentials:
                raise Exception(
                    f"Error while registering the {self.get_brick_name()} db compose. Could not find existing credentials.")

            credentials_data = cast(CredentialsDataBasic, credentials.get_data_object())
            if not isinstance(credentials_data, CredentialsDataBasic):
                raise Exception(
                    f"Error while registering the {self.get_brick_name()} db compose. Existing credentials {credentials.name} is not a basic credentials."
                )

            self._config = {
                'host': credentials_data.url,
                'port': self.PORT,
                'user': credentials_data.username,
                'password': credentials_data.password,
                'db_name': self.get_unique_name(),
                'engine': 'mariadb'
            }

        return self._config

    @abstractmethod
    def get_name(self) -> str:
        """
        Return the name of the DbManager.
        The combination of brick name and unique name must be unique accross all DbManager inheritors.
        """

    @abstractmethod
    def get_brick_name(self) -> str:
        """
        Return the brick name for this database manager.
        Must be implemented by subclasses.
        """

    @final
    def is_lazy_init(self) -> bool:
        """
        This DbManager is always lazy initialized.
        """
        return True


from abc import abstractmethod

from gws_core.core.db.abstract_db_manager import AbstractDbManager
from gws_core.core.db.db_config import DbConfig, DbMode
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.docker.docker_service import DockerService
from gws_core.user.current_user_service import AuthenticateUser
from typing_extensions import final


class LazyAbstractDbManager(AbstractDbManager):
    """
    Abstract Database Manager that automatically handles Docker container startup logic.

    Subclasses only need to define:
    - brick_name: Name of the brick
    - unique_name: Unique identifier for the database

    Everything else (host, database name, port, credentials, network configuration)
    is handled automatically.

    Example:
        class MyBrickDbManager(LazyAbstractDbManager):
            db = DatabaseProxy()
    """

    # Default configuration
    PORT = 3306

    # Internal state
    _db_username: str | None = None
    _db_password: str | None = None
    _db_host: str | None = None

    def init(self, mode: DbMode):
        """Initialize the database by starting the Docker container first"""

        if mode != 'test':
            self._start_docker_compose(mode)
        return super().init(mode)

    def _start_docker_compose(self, mode: DbMode):
        """Start the Docker container for the database"""
        try:
            brick_name = self.get_brick_name()
            unique_name = self.get_unique_name()

            Logger.info(f'Starting {self.get_unique_name()} database container')
            with AuthenticateUser.system_user():
                docker_service = DockerService()
                response_dto = docker_service.register_sqldb_compose(
                    brick_name=brick_name,
                    unique_name=f'{unique_name}_{mode}',
                    database_name=self.get_unique_name(),
                    description=f'{brick_name} brick database in {mode} mode',
                )

                self._db_username = response_dto.credentials.username
                self._db_password = response_dto.credentials.password
                self._db_host = response_dto.db_host

                Logger.info(f'{self.get_unique_name()} database container started')

        except Exception as err:
            Logger.log_exception_stack_trace(err)
            raise Exception(
                f"Error while registering the {self.get_brick_name()} db compose. Error: {err}")

    def get_config(self, mode: DbMode) -> DbConfig:
        """Get database configuration with credentials from Docker service"""

        if mode == 'test':
            return Settings.get_test_db_config()

        if not self._db_username or not self._db_password or not self._db_host:
            raise Exception(f"{self.get_brick_name()} DbManager not initialized")

        return {
            'host': self._db_host,
            'port': self.PORT,
            'user': self._db_username,
            'password': self._db_password,
            'db_name': self.get_unique_name(),
            'engine': 'mariadb'
        }

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

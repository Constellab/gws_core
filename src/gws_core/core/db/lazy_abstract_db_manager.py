
from abc import abstractmethod

from gws_core.core.db.db_config import DbConfig, DbMode
from gws_core.core.db.db_manager import AbstractDbManager
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.docker.docker_service import DockerService
from gws_core.user.current_user_service import AuthenticateUser


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

    lazy_init = True

    # Default configuration
    PORT = 3306

    # Internal state
    _db_username: str | None = None
    _db_password: str | None = None
    _db_host: str | None = None

    @classmethod
    def init(cls, mode: DbMode):
        """Initialize the database by starting the Docker container first"""

        if mode != 'test':
            cls._start_docker_compose(mode)
        return super().init(mode)

    @classmethod
    def _start_docker_compose(cls, mode: DbMode):
        """Start the Docker container for the database"""
        try:
            brick_name = cls.get_brick_name()
            unique_name = cls.get_unique_name()

            Logger.info(f'Starting {cls.get_unique_name()} database container')
            with AuthenticateUser.system_user():
                docker_service = DockerService()
                response_dto = docker_service.register_sqldb_compose(
                    brick_name=brick_name,
                    unique_name=f'{unique_name}_{mode}',
                    database_name=cls.get_unique_name(),
                    description=f'{brick_name} brick database in {mode} mode',
                )

                cls._db_username = response_dto.credentials.username
                cls._db_password = response_dto.credentials.password
                cls._db_host = response_dto.db_host

                Logger.info(f'{cls.get_unique_name()} database container started')

        except Exception as err:
            Logger.log_exception_stack_trace(err)
            raise Exception(
                f"Error while registering the {cls.get_brick_name()} db compose. Error: {err}")

    @classmethod
    def get_config(cls, mode: DbMode) -> DbConfig:
        """Get database configuration with credentials from Docker service"""

        if mode == 'test':
            return Settings.get_test_db_config()

        if not cls._db_username or not cls._db_password or not cls._db_host:
            raise Exception(f"{cls.get_brick_name()} DbManager not initialized")

        return {
            'host': cls._db_host,
            'port': cls.PORT,
            'user': cls._db_username,
            'password': cls._db_password,
            'db_name': cls.get_unique_name(),
            'engine': 'mariadb'
        }

    @classmethod
    @abstractmethod
    def get_name(cls) -> str:
        """
        Return the name of the DbManager.
        The combination of brick name and unique name must be unique accross all DbManager inheritors.
        """

    @classmethod
    @abstractmethod
    def get_brick_name(cls) -> str:
        """
        Return the brick name for this database manager.
        Must be implemented by subclasses.
        """

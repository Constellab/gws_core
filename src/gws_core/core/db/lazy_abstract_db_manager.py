
from abc import abstractmethod

from gws_core.core.db.db_config import DbConfig, DbMode
from gws_core.core.db.db_manager import AbstractDbManager
from gws_core.core.utils.logger import Logger
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

    @classmethod
    def init(cls, mode: DbMode):
        """Initialize the database by starting the Docker container first"""
        cls._start_docker_compose(mode)
        return super().init(mode)

    @classmethod
    def _start_docker_compose(cls, mode: DbMode):
        """Start the Docker container for the database"""
        try:
            brick_name = cls.get_brick_name()
            unique_name = cls.get_unique_name()

            Logger.debug(f'Starting {brick_name} database container')
            with AuthenticateUser.system_user():
                docker_service = DockerService()
                response_dto = docker_service.register_sqldb_compose(
                    brick_name=brick_name,
                    unique_name=f'{unique_name}_{mode}',
                    host=cls.get_host(mode),
                    database=cls.get_database_name(),
                    description=f'{brick_name} brick database in {mode} mode',
                    env=mode
                )

                cls._db_username = response_dto.credentials.username
                cls._db_password = response_dto.credentials.password

                Logger.debug(f'{brick_name} database container started')

        except Exception as err:
            Logger.log_exception_stack_trace(err)
            raise Exception(
                f"Error while registering the {cls.get_brick_name()} db compose. Error: {err}")

    @classmethod
    def get_config(cls, mode: DbMode) -> DbConfig:
        """Get database configuration with credentials from Docker service"""
        if not cls._db_username or not cls._db_password:
            raise Exception(f"{cls.get_brick_name()} DbManager not initialized")

        return {
            'host': cls.get_host(mode),
            'port': cls.PORT,
            'user': cls._db_username,
            'password': cls._db_password,
            'db_name': cls.get_database_name(),
            'engine': 'mariadb'
        }

    @classmethod
    def get_host(cls, mode: DbMode) -> str:
        """Generate host name based on brick name and mode"""
        return f"{cls.get_brick_name()}_db_{mode}"

    @classmethod
    def get_database_name(cls) -> str:
        """Get database name, auto-generated from brick name if not set"""
        return f"{cls.get_brick_name()}_db"

    @classmethod
    @abstractmethod
    def get_unique_name(cls) -> str:
        """
        Return the unique name for this database manager.
        Must be implemented by subclasses.
        """

    @classmethod
    @abstractmethod
    def get_brick_name(cls) -> str:
        """
        Return the brick name for this database manager.
        Must be implemented by subclasses.
        """

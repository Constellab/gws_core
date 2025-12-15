from abc import abstractmethod
from collections.abc import Callable

from peewee import DatabaseProxy, MySQLDatabase
from playhouse.shortcuts import ReconnectMixin

from gws_core.core.utils.logger import Logger
from gws_core.core.utils.utils import Utils

from .db_config import DbConfig, DbMode, SupportedDbEngine


class ReconnectMySQLDatabase(ReconnectMixin, MySQLDatabase):
    """
    MySQLDatabase class.
    Allow to auto-reconnect to the MySQL database.
    """

    pass


class AbstractDbManager:
    """
    DbManager class. Provides backend feature for managing databases.
    Implements a singleton pattern - each subclass has its own unique instance.

    Implementation must define fillowing properties

    :property db: Database Proxy
    :type db: `DatabaseProxy`
    """

    db: DatabaseProxy = None

    mode: DbMode = None

    _is_initialized = False

    # Transaction management attributes (similar to TransactionSingleton)
    _count_transaction: int = 0
    _after_commit_hooks: list[Callable] = []

    @classmethod
    @abstractmethod
    def get_instance(cls) -> "AbstractDbManager":
        """Get the singleton instance of this DbManager subclass

        Must be called implement in sub concrete classes.

        :return: The singleton instance
        :rtype: AbstractDbManager
        :raises Exception: If called on AbstractDbManager instead of a subclass
        """

    @abstractmethod
    def get_config(self, mode: DbMode) -> DbConfig:
        pass

    @abstractmethod
    def get_name(self) -> str:
        """
        Return the name of the DbManager.
        The combination of brick name and unique name must be unique accross all DbManager inheritors.
        """

    @abstractmethod
    def get_brick_name(self) -> str:
        pass

    def get_unique_name(self) -> str:
        return self.get_brick_name() + "-" + self.get_name()

    def is_lazy_init(self) -> bool:
        """
        If True, the db will be initialized after the app start, and app won't fail if db is not available
        If False, the db will be initialized immediately (not recommended), and app fails if db is not available
        """

        return True

    def init(self, mode: DbMode):
        """Initialize the DbManager"""

        if self.is_initialized():
            return
        self.mode = mode
        db_config = self.get_config(mode)

        if db_config is None:
            raise Exception(
                "The db config is not provided, did you implement the 'get_config' in your DbManager ?"
            )

        if not Utils.value_is_in_literal(db_config.engine, SupportedDbEngine):
            raise Exception(
                "gws.db.model.DbManager", "init", f"Db engine '{db_config.engine}' is not valid"
            )

        _db = ReconnectMySQLDatabase(
            db_config.db_name,
            user=db_config.user,
            password=db_config.password,
            host=db_config.host,
            port=db_config.port,
        )
        self.db.initialize(_db)
        self._is_initialized = True

    def get_db(self) -> DatabaseProxy:
        """Get the db object"""

        return self.db

    def get_engine(self) -> SupportedDbEngine:
        """Get the db object"""

        return self.get_config(self.mode)["engine"]

    def is_mysql_engine(self):
        """Test if the mysql engine is active"""

        return self.get_engine() in ["mariadb", "mysql"]

    def close_db(self):
        """Close the db connection"""

        if not self.db.is_closed():
            self.db.close()

    def connect_db(self):
        """Open the db connection"""

        if self.db.is_closed():
            self.db.connect()

    def check_connection(self) -> bool:
        """Check if the database connection is working

        :return: True if connection is working, False otherwise
        :rtype: bool
        """
        try:
            # Try to execute a simple query to verify the connection
            self.db.execute_sql("SELECT 1")
            return True
        except Exception as e:
            Logger.error(f"Database connection check failed: {e}")
            return False

    def create_tables(self, models: list[type]) -> None:
        """Create the tables for the provided models"""

        if not models or len(models) == 0:
            return

        self.db.create_tables(models)

    def drop_tables(self, models: list[type]) -> None:
        """Drop the tables for the provided models"""

        if not models or len(models) == 0:
            return

        self.db.drop_tables(models)

    def execute_sql(self, sql: str) -> None:
        """Execute the provided sql command"""

        self.db.execute_sql(sql)

    def is_initialized(self) -> bool:
        """Return if the db manager was initialized"""

        return self._is_initialized

    def _increment_transaction(self) -> None:
        """Increment the transaction counter"""
        self._count_transaction += 1

    def _decrement_transaction(self) -> None:
        """Decrement the transaction counter"""
        self._count_transaction -= 1

        self._count_transaction = max(self._count_transaction, 0)

    def has_transaction(self) -> bool:
        """Check if there is an active transaction"""
        return self._count_transaction > 0

    def register_after_commit_hook(self, hook: Callable) -> None:
        """Register a hook to be called after a transaction is committed

        :param hook: Hook to register
        :type hook: Callable
        """
        self._after_commit_hooks.append(hook)

    def _run_after_commit_hooks(self) -> None:
        """Run all hooks registered to be called after a transaction is committed"""
        if not self._after_commit_hooks:
            return
        for hook in self._after_commit_hooks:
            try:
                hook()
            except Exception as e:
                # Log the exception but continue with other hooks
                Logger.error(f"Error running after commit hook: {e}")
        self._after_commit_hooks = []

    ############################### CLASS METHODS ###############################

    @classmethod
    def transaction(cls, nested_transaction: bool = False) -> Callable:
        """Decorator to create a new transaction around a method
        If an exception is raised, the transaction is rolled back

        Can also be used as a context manager.

        :param nested_transaction: if False only 1 transaction is created at a time and it waits for the transaction
        to finish before creating a new one. If True, a transaction is created each time this method is called
        :type nested_transaction: bool

        Usage as decorator:
            @GwsCoreDbManager.get_instance().transaction()
            def my_method():
                pass

        """

        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                db_manager = cls.get_instance()
                if db_manager is None:
                    raise Exception(
                        "The DbManager instance is not available, did you implement the 'get_instance' in your DbManager ?"
                    )
                # If we are in unique transaction mode and a transaction already exists,
                # don't create a transaction
                if not nested_transaction and db_manager.has_transaction():
                    return func(*args, **kwargs)

                db_manager._increment_transaction()
                try:
                    with db_manager.db.transaction() as nested_txn:
                        try:
                            result = func(*args, **kwargs)
                        except Exception as err:
                            nested_txn.rollback()
                            raise err
                        nested_txn.commit()
                        db_manager._run_after_commit_hooks()
                finally:
                    db_manager._decrement_transaction()

                return result

            return wrapper

        return decorator

    @classmethod
    def get_db_managers(cls) -> set["AbstractDbManager"]:
        """Get all the classes that inherit this class"""
        db_managers = set(cls.__subclasses__()).union(
            [s for c in cls.__subclasses__() for s in c.get_db_managers()]
        )

        return {
            db_manager.get_instance()
            for db_manager in db_managers
            if db_manager.get_instance() is not None
        }

    @classmethod
    def reconnect_dbs(cls) -> None:
        """Reconnect all db managers"""
        for db_manager in cls.get_db_managers():
            if db_manager.is_initialized():
                db_manager.close_db()
                db_manager.connect_db()

    @classmethod
    def close_dbs(cls) -> None:
        """Close all db managers"""
        for db_manager in cls.get_db_managers():
            if db_manager.is_initialized():
                db_manager.close_db()


from peewee import (
    ColumnMetadata,
    DatabaseProxy,
    ForeignKeyField,
    ForeignKeyMetadata,
    Metadata,
    ModelSelect,
)
from peewee import Model as PeeweeModel

from gws_core.core.db.abstract_db_manager import AbstractDbManager
from gws_core.core.db.gws_core_db_manager import GwsCoreDbManager

from ...core.exception.exceptions import BadRequestException
from .base import Base


class ModelMetadata(Metadata):
    db_manager: AbstractDbManager
    # If False, the model does not represent a table in the database
    is_table: bool


class BaseModel(Base, PeeweeModel):
    """BaseModel that contains no column but management for Tables (create, delete, foreign key...)"""

    @classmethod
    def create_table(cls, *args, **kwargs):
        """
        Create model table
        """

        if not cls.is_table() or cls.table_exists():
            return
        super().create_table(*args, **kwargs)
        cls.after_table_creation()

    @classmethod
    def after_table_creation(cls) -> None:
        """Method call after the table is created

        Usefull to create the full text indexes
        """

    @classmethod
    def after_all_tables_init(cls) -> None:
        """Method call after all the table are inited

        Useful when use DeferredForeignKey to create the foreign key manually latter
        """

    @classmethod
    def create_foreign_key_if_not_exist(cls, field: ForeignKeyField) -> None:
        """Create a foreign key for a Foreign key field only if the foreign key does not exists

        :param field: [description]
        :type field: ForeignKeyField
        """
        if not cls.foreign_key_exists(field.column_name):
            cls._schema.create_foreign_key(field)

    @classmethod
    def create_full_text_index(cls, columns: list[str], index_name: str) -> None:
        """Method to create a full text index

        :param columns: [description]
        :type columns: List[str]
        """
        if not cls.get_db_manager().is_mysql_engine():
            return
        cls.execute_sql(
            f"CREATE FULLTEXT INDEX {index_name} ON {cls.get_table_name()}({','.join(columns)})"
        )

    @classmethod
    def foreign_key_exists(cls, column_name: str) -> bool:
        foreign_keys: list[ForeignKeyMetadata] = cls._schema.database.get_foreign_keys(
            cls.get_table_name()
        )
        return len([x for x in foreign_keys if x.column == column_name]) > 0

    @classmethod
    def drop_table(cls, *args, **kwargs):
        """
        Drop model table
        """

        if not cls.table_exists():
            return

        super().drop_table(*args, **kwargs)

    @classmethod
    def get_table_name(cls) -> str | None:
        """
        Returns the table name of this class

        :return: The table name
        :rtype: `str`
        """
        if not cls.is_table():
            return None

        return cls.get_metadata().table_name

    @classmethod
    def is_table(cls) -> bool:
        """
        Returns True if the class has a table name defined

        :return: True if the class has a table name defined
        :rtype: `bool`
        """
        return cls.get_metadata().is_table

    @classmethod
    def column_exists(cls, column_name: str) -> bool:
        """
        Returns True if the column exists in the table

        :param column_name: The column name
        :type column_name: `str`
        :return: True if the column exists
        :rtype: `bool`
        """
        columns: list[ColumnMetadata] = cls.get_db().get_columns(cls.get_table_name())
        return len([x for x in columns if x.name == column_name]) > 0

    @classmethod
    def index_exists(cls, index_name: str) -> bool:
        """
        Returns True if the index exists in the table

        :param index_name: The index name
        :type index_name: `str`
        :return: True if the index exists
        :rtype: `bool`
        """
        indexes = cls.get_db().get_indexes(cls.get_table_name())
        return len([x for x in indexes if x.name == index_name]) > 0

    @classmethod
    def execute_sql(cls, query: str):
        """
        Execute a raw SQL query. Can use the [TABLE_NAME] to replace by the table name

        :param query: The query to execute
        :type query: `str`
        """
        cls.get_db().execute_sql(query.replace("[TABLE_NAME]", cls.get_table_name()))

    @classmethod
    def get_db(cls) -> DatabaseProxy:
        return cls.get_db_manager().db

    @classmethod
    def get_db_manager(cls) -> AbstractDbManager:
        """
        Returns the (current) DbManager of this model

        :return: The db manager
        :rtype: `DbManager`
        """

        return cls.get_metadata().db_manager

    @classmethod
    def get_metadata(cls) -> ModelMetadata:
        return cls._meta

    @classmethod
    def search(cls, phrase: str, modifier: str = None) -> ModelSelect:
        """
        Performs full-text search on the field. Must be overrided by child class to work
        :param phrase: The phrase to search
        :type phrase: `str`
        :param in_boolean_mode: True to search in boolean mode, False otherwise
        :type in_boolean_mode: `bool`
        """
        raise BadRequestException("This entity does not support search")

    @classmethod
    def is_mysql_engine(cls):
        return cls.get_db_manager().is_mysql_engine()

    def save(self, *args, **kwargs) -> "BaseModel":
        if not self.is_table():
            raise Exception(
                f"The class '{type(self).__name__}' is not a table, cannot save it. Set is_table to True in the Meta class to make it a table."
            )

        super().save(*args, **kwargs)

        return self

    class Meta:
        db_manager = GwsCoreDbManager.get_instance()
        is_table: bool = False
        database = db_manager.db
        legacy_table_names = False

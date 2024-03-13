

from typing import List, Type

from peewee import (ColumnMetadata, DatabaseProxy, ForeignKeyField,
                    ForeignKeyMetadata)
from peewee import Model as PeeweeModel
from peewee import ModelSelect

from gws_core.core.db.db_manager import AbstractDbManager
from gws_core.core.db.gws_core_db_manager import GwsCoreDbManager

from ...core.exception.exceptions import BadRequestException
from .base import Base


def format_table_name(model: Type['BaseModel']) -> str:
    return model._table_name.lower() if hasattr(model, "_table_name") else None


class BaseModel(Base, PeeweeModel):
    """ BaseModel that contains no column but management for Tables (create, delete, foreign key...)
    """

    _db_manager = GwsCoreDbManager

    @classmethod
    def create_table(cls, *args, **kwargs):
        """
        Create model table
        """

        if not hasattr(cls, "_table_name") or cls.table_exists():
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
    def create_full_text_index(cls, columns: List[str], index_name: str) -> None:
        """Method to create a full text index

        :param columns: [description]
        :type columns: List[str]
        """
        if not cls.get_db_manager().is_mysql_engine():
            return
        cls.get_db_manager().db.execute_sql(
            f"CREATE FULLTEXT INDEX {index_name} ON {cls.get_table_name()}({','.join(columns)})")

    @classmethod
    def foreign_key_exists(cls, column_name: str) -> bool:
        foreign_keys: List[ForeignKeyMetadata] = cls._schema.database.get_foreign_keys(cls._table_name)
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
    def get_table_name(cls) -> str:
        """
        Returns the table name of this class

        :return: The table name
        :rtype: `str`
        """

        return format_table_name(cls)

    @classmethod
    def column_exists(cls, column_name: str) -> bool:
        """
        Returns True if the column exists in the table

        :param column_name: The column name
        :type column_name: `str`
        :return: True if the column exists
        :rtype: `bool`
        """
        columns: List[ColumnMetadata] = cls.get_db().get_columns(cls.get_table_name())
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
    def get_db(cls) -> DatabaseProxy:
        return cls.get_db_manager().db

    @classmethod
    def get_db_manager(cls) -> Type[AbstractDbManager]:
        """
        Returns the (current) DbManager of this model

        :return: The db manager
        :rtype: `DbManager`
        """

        return cls._db_manager

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

    def save(self, *args, **kwargs) -> 'BaseModel':
        if not hasattr(self, "_table_name"):
            raise Exception(f"The class '{type(self).__name__}' does not have the attribute '_table_name'")

        super().save(*args, **kwargs)

        return self

    class Meta:
        database = GwsCoreDbManager.db
        table_function = format_table_name

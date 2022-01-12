

from typing import List, Type

from peewee import ForeignKeyField, ForeignKeyMetadata
from peewee import Model as PeeweeModel

from ..db.db_manager import DbManager
from .base import Base


def format_table_name(model: Type['BaseModel']) -> str:
    return model._table_name.lower() if hasattr(model, "_table_name") else None


class BaseModel(Base, PeeweeModel):
    """ BaseModel that contains no column but management for Tables (create, delete, foreign key...)
    """

    _db_manager = DbManager

    @classmethod
    def create_table(cls, *args, **kwargs):
        """
        Create model table
        """

        if not hasattr(cls, "_table_name") or cls.table_exists():
            return
        super().create_table(*args, **kwargs)

    @classmethod
    def after_table_init(cls) -> None:
        """Method call after all the table are inited

        Useful when use DeferredForeignKey to create the foreign key manually latter
        """

    @classmethod
    def create_foreign_key_if_not_exist(cls, field: ForeignKeyField) -> None:
        """Create a foreign key for a Foreign key field only if the foreign key does not exists

        :param field: [description]
        :type field: ForeignKeyField
        """
        if not cls.foreign_key_exists(field):
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
    def foreign_key_exists(cls, field: ForeignKeyField) -> bool:
        foreign_keys: List[ForeignKeyMetadata] = cls._schema.database.get_foreign_keys(cls._table_name)
        column_name = field.column_name
        return len([x for x in foreign_keys if x.column == column_name]) > 0

    # -- D --

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
    def get_db_manager(cls) -> Type[DbManager]:
        """
        Returns the (current) DbManager of this model

        :return: The db manager
        :rtype: `DbManager`
        """

        return cls._db_manager

    @classmethod
    def is_sqlite3_engine(cls):
        return cls.get_db_manager().get_engine() == "sqlite3"

    @classmethod
    def is_mysql_engine(cls):
        return cls.get_db_manager().get_engine() in ["mysql", "mariadb"]

    def save(self, *args, **kwargs) -> 'BaseModel':
        super().save(*args, **kwargs)

        return self

    class Meta:
        database = DbManager.db
        table_function = format_table_name

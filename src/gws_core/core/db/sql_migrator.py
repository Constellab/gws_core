# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from typing import Any, List

from gws_core.core.model.base_model import BaseModel
from peewee import DatabaseProxy, Field
from playhouse.migrate import MySQLMigrator


class SqlMigrator:
    """This object is to call sql migration script using peewee
    """

    migrator: MySQLMigrator

    _operations: List[Any]

    def __init__(self, db: DatabaseProxy) -> None:
        self.migrator = MySQLMigrator(db)
        self._operations = []

    def add_migration(self, operation) -> None:
        self._operations.append(operation)

    def add_column_if_not_exists(self, model: BaseModel, field: Field) -> bool:
        if model.column_exists(field.column_name):
            return False
        self.add_column(model, field)
        return True

    def add_column(self, model: BaseModel, field: Field) -> None:
        self._operations.append(self.migrator.add_column(model.get_table_name(), field.column_name, field))

    def alter_column_type(self, model: BaseModel, field_name: str, field: Field) -> None:
        self._operations.append(self.migrator.alter_column_type(model.get_table_name(), field_name, field))

    def migrate(self) -> None:
        for operation in self._operations:
            operation.run()

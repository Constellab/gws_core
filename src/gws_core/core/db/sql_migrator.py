
from typing import Any, List, Type

from peewee import DatabaseProxy, Field
from playhouse.migrate import MySQLMigrator

from gws_core.core.model.base_model import BaseModel
from gws_core.resource.resource_model import ResourceModel


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

    def add_column_if_not_exists(self, model_type: Type[BaseModel], field: Field,
                                 column_name: str = None) -> bool:
        new_column_name = column_name or field.column_name
        if not new_column_name:
            raise Exception("Column name must be provided")
        if model_type.column_exists(new_column_name):
            return False
        self._operations.append(self.migrator.add_column(model_type.get_table_name(), new_column_name, field))
        return True

    def drop_column_if_exists(self, model_type: Type[BaseModel], column_name: str) -> bool:
        if not model_type.column_exists(column_name):
            return False
        self._operations.append(self.migrator.drop_column(model_type.get_table_name(), column_name))
        return True

    def alter_column_type(self, model_type: Type[BaseModel], field_name: str, field: Field) -> None:
        self._operations.append(self.migrator.alter_column_type(model_type.get_table_name(), field_name, field))

    def rename_column_if_exists(self, model_type: Type[BaseModel], old_name: str, new_name: str) -> bool:
        if not model_type.column_exists(old_name):
            return False
        self._operations.append(self.migrator.rename_column(model_type.get_table_name(), old_name, new_name))
        return True

    def drop_index_if_exists(self, model_type: Type[BaseModel], index_name: str) -> bool:
        if not model_type.index_exists(index_name):
            return False
        self._operations.append(self.migrator.drop_index(model_type.get_table_name(), index_name))
        return True

    def add_index_if_not_exists(
            self, model_type: Type[BaseModel], index_name: str, columns: List[str],
            unique: bool = False) -> bool:
        if model_type.index_exists(index_name):
            return False
        self._operations.append(self.migrator.add_index(model_type.get_table_name(), columns, unique))
        return True

    def rename_table_if_exists(self, model_type: Type[BaseModel], old_name: str) -> bool:
        if model_type.table_exists():
            return False
        self._operations.append(self.migrator.rename_table(old_name, model_type.get_table_name()))
        return True

    def migrate(self) -> None:
        for operation in self._operations:
            operation.run()

    ############################### CLASS METHODS ####################################
    # thoses methods are executed directly, no need to create an instance of the class and call the method

    @classmethod
    def drop_table_if_exists(cls, db: DatabaseProxy, model_type: Type[BaseModel]) -> bool:
        db.drop_tables([model_type])
        return True

    @classmethod
    def rename_resource_typing_name(cls, db: DatabaseProxy, old_typing_name: str, new_typing_name: str) -> None:
        db.execute_sql(
            f"UPDATE gws_resource SET resource_typing_name = '{new_typing_name}' where resource_typing_name = '{old_typing_name}'")
        db.execute_sql(f"UPDATE gws_task SET data = REPLACE(data, '{old_typing_name}', '{new_typing_name}')")
        db.execute_sql(
            f"UPDATE gws_scenario_template SET data = REPLACE(data, '{old_typing_name}', '{new_typing_name}')")

    @classmethod
    def rename_process_typing_name(cls, db: DatabaseProxy, old_typing_name: str, new_typing_name: str) -> None:
        db.execute_sql(
            f"UPDATE gws_task SET process_typing_name = '{new_typing_name}' where process_typing_name = '{old_typing_name}'")
        db.execute_sql(
            f"UPDATE gws_protocol SET process_typing_name = '{new_typing_name}' where process_typing_name = '{old_typing_name}'")

        db.execute_sql(
            f"UPDATE gws_scenario_template SET data = REPLACE(data, '{old_typing_name}', '{new_typing_name}')")

    @classmethod
    def rename_r_field_of_resource_type(
            cls, resource_typing_name: str, old_field_name: str, new_field_name: str) -> None:
        """
        Rename a field in the resource model for all resources of a given typing name.

        :param resource_typing_name: The typing name of the resource
        :type resource_typing_name: str
        :param old_field_name: The name of the field to rename
        :type old_field_name: str
        :param new_field_name: The new name of the field
        :type new_field_name: str
        """
        resource_models: List[ResourceModel] = ResourceModel.select().where(
            (ResourceModel.resource_typing_name == resource_typing_name)
        )

        for resource_model in resource_models:
            cls.rename_resource_model_r_field(resource_model, old_field_name, new_field_name)

    @classmethod
    def rename_resource_model_r_field(
            cls, resource_model: ResourceModel, old_field_name: str, new_field_name: str) -> None:
        """
        Rename a field in the resource model for a specific resource model.

        :param resource_model: The resource model to update
        :type resource_model: ResourceModel
        :param old_field_name: The name of the field to rename
        :type old_field_name: str
        :param new_field_name: The new name of the field
        :type new_field_name: str
        """

        kv_store = resource_model.get_kv_store()

        if old_field_name in kv_store:
            old_field = kv_store.get(old_field_name)

            kv_store._lock = False
            kv_store[new_field_name] = old_field
            del kv_store[old_field_name]
            kv_store._lock = True

            resource_model.save(skip_hook=True)

    @classmethod
    def set_r_field_of_resource_type(
            cls, resource_typing_name: str, field_name: str, value: Any) -> None:
        """
        Set the value of an R field for all resources of a given typing name.

        :param resource_typing_name: The typing name of the resource
        :type resource_typing_name: str
        :param field_name: The name of the field to set
        :type field_name: str
        :param value: The value to set for the field
        :type value: Any
        """
        resource_models: List[ResourceModel] = list(ResourceModel.select().where(
            (ResourceModel.resource_typing_name == resource_typing_name)
        ))

        for resource_model in resource_models:
            cls.set_resource_model_r_field(resource_model, field_name, value)

    @classmethod
    def set_resource_model_r_field(
            cls, resource_model: ResourceModel, field_name: str, value: Any) -> None:
        """
        Set the value of an R field for a resource model.

        :param resource_model: The resource model to update
        :type resource_model: ResourceModel
        :param field_name: The name of the field to set
        :type field_name: str
        :param value: The value to set for the field
        :type value: Any
        """
        kv_store = resource_model.get_kv_store()
        kv_store._lock = False
        kv_store[field_name] = value
        kv_store._lock = True

        resource_model.save(skip_hook=True)



from typing import List, Tuple, Type

from peewee import DatabaseProxy

from ..utils.logger import Logger
from .base_model import BaseModel


class BaseModelService:
    """Service to handle BaseModel. Table creation and deletion

    :return: [description]
    :rtype: [type]
    """

    __model_types: List[Type[BaseModel]] = None

    @classmethod
    def get_base_model_types(cls) -> List[Type[BaseModel]]:
        """Return all the sub classes of BaseModel

        :return: [description]
        :rtype: List[Type[BaseModel]]
        """
        if not getattr(cls, '__model_types', None):
            cls.__model_types: List[Type[BaseModel]] = BaseModel.inheritors()

        return cls.__model_types

    @classmethod
    def create_tables(cls, models: List[type] = None, model_type: type = None):
        """
        Create tables (if they don't exist)

        :param models: List of model tables to create
        :type models: `List[type]`
        :param instance: If provided, only the tables of the models that are instances of `model_type` will be create
        :type model_type: `type`
        """

        db_list, model_list = cls._get_db_and_model_types(models)
        for db in db_list:
            i = db_list.index(db)
            models = [t for t in model_list[i] if not t.table_exists()]
            if model_type:
                models = [t for t in models if isinstance(t, model_type)]
            db.create_tables(models)

        # Create the foreign keys after if necessary (for DeferredForeignKey for example)
        for models in model_list:
            for model in models:
                model.create_foreign_keys()

    @classmethod
    def drop_tables(cls, model_types: List[Type[BaseModel]] = None, model_type: type = None):
        """
        Drops tables (if they exist)

        :param models: List of model tables to drop
        :type models: `List[type]`
        :param instance: If provided, only the tables of the models that are instances of `model_type` will be droped
        :type model_type: `type`
        """

        db_list, model_list = cls._get_db_and_model_types(model_types)
        for db in db_list:
            i = db_list.index(db)
            models: List[BaseModel] = [
                t for t in model_list[i] if t.table_exists()]
            if model_type:
                models = [t for t in models if isinstance(t, model_type)]

            if len(models) == 0:
                Logger.debug("No table to drop")
                return

            # Disable foreigne key on my sql to drop the tables
            if models[0].is_mysql_engine():
                db.execute_sql("SET FOREIGN_KEY_CHECKS=0")
            # Drop all the tables
            db.drop_tables(models)

            if models[0].is_mysql_engine():
                db.execute_sql("SET FOREIGN_KEY_CHECKS=1")

    @classmethod
    def _get_db_and_model_types(cls, models: list = None) -> Tuple[List[DatabaseProxy], List[List[Type[BaseModel]]]]:
        if not models:
            models = cls.get_base_model_types()
        db_list = []
        model_list = []
        for t in models:
            db = t._db_manager.db
            if db in db_list:
                i = db_list.index(db)
                model_list[i].append(t)
            else:
                db_list.append(db)
                model_list.append([t])
        return db_list, model_list

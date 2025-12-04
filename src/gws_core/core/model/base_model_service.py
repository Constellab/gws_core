from dataclasses import dataclass
from typing import Dict, List, Type

from gws_core.core.db.abstract_db_manager import AbstractDbManager

from ..utils.logger import Logger
from .base_model import BaseModel


@dataclass
class DbWithModels:
    db_manager: AbstractDbManager
    models: List[Type[BaseModel]]


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
        if not getattr(cls, "__model_types", None):
            cls.__model_types: List[Type[BaseModel]] = BaseModel.inheritors()

        return cls.__model_types

    @classmethod
    def create_all_tables(cls):
        """
        Create tables (if they don't exist)

        :param models: List of model tables to create
        :type models: `List[type]`
        :param instance: If provided, only the tables of the models that are instances of `model_type` will be create
        :type model_type: `type`
        """

        all_db_with_models = cls._get_all_db_and_model_types()
        for db_with_models in all_db_with_models.values():
            cls._create_database_tables(db_with_models)

    @classmethod
    def create_database_tables(cls, db_manager: AbstractDbManager):
        """
        Create tables (if they don't exist) for the provided DbManager

        :param db_manager: The DbManager class to create the tables for
        :type db_manager: AbstractDbManager
        """

        all_db_with_models = cls._get_all_db_and_model_types()

        if db_manager.get_unique_name() not in all_db_with_models:
            raise Exception(f"No model found for the db manager '{db_manager.get_unique_name()}'")

        db_with_models = all_db_with_models[db_manager.get_unique_name()]
        cls._create_database_tables(db_with_models)

    @classmethod
    def _create_database_tables(cls, db_with_models: DbWithModels):
        """
        Create tables (if they don't exist) for the provided DbManager

        :param db_manager: The DbManager class to create the tables for
        :type db_manager: AbstractDbManager
        """

        db_manager = db_with_models.db_manager

        # Filter classes that have a table name (not abstract) and that don't exist yet
        models = [t for t in db_with_models.models if not t.table_exists()]

        db_manager.create_tables(models)

        # Create the foreign keys after if necessary (for DeferredForeignKey for example)
        for model in db_with_models.models:
            model.after_all_tables_init()

    @classmethod
    def drop_tables(cls):
        """
        Drops tables (if they exist)

        :param models: List of model tables to drop
        :type models: `List[type]`
        :param instance: If provided, only the tables of the models that are instances of `model_type` will be droped
        :type model_type: `type`
        """

        all_db_with_models = cls._get_all_db_and_model_types()
        for db_with_models in all_db_with_models.values():
            models: List[Type[BaseModel]] = [t for t in db_with_models.models if t.table_exists()]

            if len(models) == 0:
                Logger.debug("No table to drop")
                return

            # Disable foreigne key on my sql to drop the tables
            if models[0].is_mysql_engine():
                db_with_models.db_manager.execute_sql("SET FOREIGN_KEY_CHECKS=0")
            # Drop all the tables
            db_with_models.db_manager.drop_tables(models)

            if models[0].is_mysql_engine():
                db_with_models.db_manager.execute_sql("SET FOREIGN_KEY_CHECKS=1")

    @classmethod
    def _get_all_db_and_model_types(cls) -> Dict[str, DbWithModels]:
        db_with_models: Dict[str, DbWithModels] = {}
        models = cls.get_base_model_types()

        for model in models:
            if not model.is_table():
                continue
            db_manager = model.get_db_manager()

            if db_manager is None:
                raise Exception(
                    f"The model '{model.__name__}' has no db manager. Please set the db_manager in the Meta class of the model."
                )

            if not isinstance(db_manager, AbstractDbManager):
                raise Exception(
                    f"The model '{model.__name__}' has a db manager that is not an instance of AbstractDbManager. Please check the db_manager in the Meta class of the model."
                )

            # Check that the database and db_manager match
            if db_manager.get_db() != model.get_metadata().database:
                raise Exception(
                    f"The model '{model.__name__}' has a db manager that does not match its database. Please check the db_manager and database in the Meta class of the model."
                )

            if db_manager.get_unique_name() not in db_with_models:
                db_with_models[db_manager.get_unique_name()] = DbWithModels(
                    db_manager=db_manager, models=[]
                )

            db_with_model = db_with_models[db_manager.get_unique_name()]
            db_with_model.models.append(model)

        return db_with_models

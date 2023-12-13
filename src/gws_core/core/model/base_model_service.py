# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, List, Type

from gws_core.brick.brick_helper import BrickHelper
from gws_core.brick.brick_service import BrickService
from gws_core.core.db.db_manager import AbstractDbManager
from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.utils.settings import Settings

from ..utils.logger import Logger
from .base_model import BaseModel


class DbWithModels(BaseModelDTO):
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
        if not getattr(cls, '__model_types', None):
            cls.__model_types: List[Type[BaseModel]] = BaseModel.inheritors()

        return cls.__model_types

    @classmethod
    def create_tables(cls):
        """
        Create tables (if they don't exist)

        :param models: List of model tables to create
        :type models: `List[type]`
        :param instance: If provided, only the tables of the models that are instances of `model_type` will be create
        :type model_type: `type`
        """

        db_with_models = cls._get_db_and_model_types()
        for db_with_model in db_with_models:
            db_manager = db_with_model.db_manager
            try:

                models = [t for t in db_with_model.models if not t.table_exists()]

                db_manager.db.create_tables(models)
            except Exception as err:
                # if we can't load the gws_core db, raise error
                if db_manager.get_brick_name() == Settings.get_gws_core_brick_name():
                    raise err

                # if this is another DB, log exception and continues
                Logger.log_exception_stack_trace(err)

                # get the brick from the first model type
                brick_info = BrickHelper.get_brick_info(db_manager.get_brick_name())
                if brick_info is not None:
                    BrickService.log_brick_message(
                        brick_info["name"],
                        f"Cannot initialize databse {db_manager.get_unique_name()}. Error : {err}", "CRITICAL")

        # Create the foreign keys after if necessary (for DeferredForeignKey for example)
        for db_with_model in db_with_models:
            for model in db_with_model.models:
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

        db_with_models = cls._get_db_and_model_types()
        for db_with_model in db_with_models:

            models: List[Type[BaseModel]] = [
                t for t in db_with_model.models if t.table_exists()]

            if len(models) == 0:
                Logger.debug("No table to drop")
                return

            # Disable foreigne key on my sql to drop the tables
            if models[0].is_mysql_engine():
                db_with_model.db_manager.db.execute_sql("SET FOREIGN_KEY_CHECKS=0")
            # Drop all the tables
            db_with_model.db_manager.db.drop_tables(models)

            if models[0].is_mysql_engine():
                db_with_model.db_manager.db.execute_sql("SET FOREIGN_KEY_CHECKS=1")

    @classmethod
    def _get_db_and_model_types(cls) -> List[DbWithModels]:
        db_with_models: Dict[str, DbWithModels] = {}
        models = cls.get_base_model_types()

        for model in models:
            db_manager = model.get_db_manager()

            if db_manager.get_unique_name() not in db_with_models:
                db_with_models[db_manager.get_unique_name()] = DbWithModels(
                    db_manager=db_manager,
                    models=[]
                )

            db_with_model = db_with_models[db_manager.get_unique_name()]
            db_with_model.models.append(model)

        return list(db_with_models.values())

# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import List, Tuple, Type

from peewee import DatabaseProxy

from ..core.classes.paginator import Paginator
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..core.model.model import Model
from ..core.service.base_service import BaseService
from ..core.utils.logger import Logger
from .typing_manager import TypingManager


class ModelService(BaseService):

    # -- C --

    # @classmethod
    # def create_view_model(cls, type_str: str, uri: str, data: RenderingDTO) -> ViewModel:
    #     """
    #     View a model

    #     :param type: The type of the model
    #     :type type: `str`
    #     :param uri: The uri of the model
    #     :type uri: `str`
    #     :param data: The rendering data
    #     :type data: `dict`
    #     :return: A model if `as_json == False`, a dictionary if `as_json == True=
    #     :rtype: `gws.db.model.Model`, `dict`
    #     """

    #     model_type: Type[Model] = Utils.get_model_type(type_str)
    #     if model_type is None:
    #         raise NotFoundException(
    #             detail=f"Model type '{type_str}' not found")
    #     try:
    #         view_model = model_type.get(model_type.uri == uri).create_view_model(
    #             data=data.dict())
    #         return view_model
    #     except Exception as err:
    #         raise BadRequestException(
    #             detail=f"Cannot create a view_model for the model of type '{type_str}' and uri '{uri}'") from err

    @classmethod
    def count_model(cls, typing_name: str) -> int:
        """
        Counts models
        """

        model_type: Type[Model] = TypingManager.get_type_from_name(typing_name)

        return cls.count_model_from_type(model_type)

    @classmethod
    def count_model_from_type(cls, model_type: Type[Model]) -> int:
        """
        Counts models
        """

        return model_type.select().count()

    # -- F --

    @classmethod
    def fetch_model(cls, typing_name: str, uri: str) -> Model:
        """
        Fetch a model

        :param type: The type of the model
        :type type: `str`
        :param uri: The uri of the model
        :type uri: `str`
        :return: A model
        :rtype: instance of `gws.db.model.Model`
        """

        return TypingManager.get_object_with_typing_name_and_uri(typing_name, uri)

    @classmethod
    def fetch_list_of_models(cls,
                             typing_name: str,
                             page: int = 0, number_of_items_per_page: int = 20) -> Paginator[Model]:

        model_type: Type[Model] = TypingManager.get_type_from_name(typing_name)

        if not issubclass(model_type, Model):
            raise BadRequestException("The requested type is not a Model")

        number_of_items_per_page = min(
            number_of_items_per_page, cls._number_of_items_per_page)

        query = model_type.select().order_by(model_type.creation_datetime.desc())
        return Paginator(
            query, page=page, number_of_items_per_page=number_of_items_per_page)

    # -- G --

    @classmethod
    def get_model_types(cls):
        if not getattr(cls, '__model_types', None):
            cls.__model_types: List[Type[Model]] = Model.inheritors()

        return cls.__model_types

    # -- I --

    # -- R --

    @classmethod
    def register_all_processes_and_resources(cls) -> None:
        TypingManager.save_object_types_in_db()

    @classmethod
    def archive_model(cls, typing_name: str, uri: str) -> Model:
        return cls._set_archive(typing_name, uri, True)

    @classmethod
    def unarchive_model(cls, typing_name: str, uri: str) -> Model:
        return cls._set_archive(typing_name, uri, False)

    @classmethod
    def _set_archive(cls, typing_name: str, uri: str, archive: bool) -> Model:
        model: Model = TypingManager.get_object_with_typing_name_and_uri(typing_name, uri)

        return model.archive(archive)

    # -- V --

    @classmethod
    def verify_model_hash(cls, typing_name: str, uri: str) -> bool:
        """
        Verify model hash

        :param type: The type of the model
        :type type: `str`
        :param uri: The uri of the model
        :type uri: `str`
        :return: True if the hash is valid, False otherwise
        :rtype: `bool`
        """

        model: Model = TypingManager.get_object_with_typing_name_and_uri(typing_name, uri)
        return model.verify_hash()

    @classmethod
    def search(cls, typing_name: str, search_text: str,
               page: int = 0, number_of_items_per_page: int = 20) -> Paginator[Model]:
        base_type: Type[Model] = TypingManager.get_type_from_name(typing_name)

        query = base_type.search(search_text)
        return Paginator(query, page=page, number_of_items_per_page=number_of_items_per_page,
                         nb_max_of_items_per_page=cls._number_of_items_per_page)

    ############################################ DB ######################################

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

    @classmethod
    def drop_tables(cls, model_types: List[Type[Model]] = None, model_type: type = None):
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
            models: List[Model] = [
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
    def _get_db_and_model_types(cls, models: list = None) -> Tuple[DatabaseProxy, List[Type[Model]]]:
        if not models:
            models = ModelService.get_model_types()
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

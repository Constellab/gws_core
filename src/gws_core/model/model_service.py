# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Dict, List, Tuple, Type, Union

from peewee import DatabaseProxy

from ..core.classes.paginator import Paginator
from ..core.decorator.transaction import transaction
from ..core.dto.rendering_dto import RenderingDTO
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..core.exception.exceptions.not_found_exception import NotFoundException
from ..core.model.model import Model
from ..core.service.base_service import BaseService
from ..core.utils.logger import Logger
from ..core.utils.utils import Utils
from ..process.process_model import ProcessModel
from ..resource.resource_model import ResourceModel
from .typing_manager import TypingManager
from .view_model import ViewModel


class ModelService(BaseService):

    # -- A --

    @classmethod
    def archive_model(cls, type_str: str, uri: str) -> dict:
        return cls.__set_archive_status(True, type_str, uri)

    # -- C --

    @classmethod
    def create_view_model(cls, type_str: str, uri: str, data: RenderingDTO) -> ViewModel:
        """
        View a model

        :param type: The type of the model
        :type type: `str`
        :param uri: The uri of the model
        :type uri: `str`
        :param data: The rendering data
        :type data: `dict`
        :return: A model if `as_json == False`, a dictionary if `as_json == True=
        :rtype: `gws.db.model.Model`, `dict`
        """

        t = Utils.get_model_type(type_str)
        if t is None:
            raise NotFoundException(
                detail=f"Model type '{type_str}' not found")
        try:
            view_model = t.get(t.uri == uri).create_view_model(
                data=data.dict())
            return view_model
        except Exception as err:
            raise BadRequestException(
                detail=f"Cannot create a view_model for the model of type '{type_str}' and uri '{uri}'") from err

    @classmethod
    def create_tables(cls, models: List[type] = None, model_type: type = None):
        """
        Create tables (if they don't exist)

        :param models: List of model tables to create
        :type models: `List[type]`
        :param instance: If provided, only the tables of the models that are instances of `model_type` will be create
        :type model_type: `type`
        """

        db_list, model_list = cls.get_db_and_model_types(models)
        for db in db_list:
            i = db_list.index(db)
            models = [t for t in model_list[i] if not t.table_exists()]
            if model_type:
                models = [t for t in models if isinstance(t, model_type)]
            db.create_tables(models)

    @classmethod
    def drop_tables(cls, models: List[type] = None, model_type: type = None):
        """
        Drops tables (if they exist)

        :param models: List of model tables to drop
        :type models: `List[type]`
        :param instance: If provided, only the tables of the models that are instances of `model_type` will be droped
        :type model_type: `type`
        """

        db_list, model_list = cls.get_db_and_model_types(models)
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
    def count_model(cls, type: str) -> int:
        """
        Counts models
        """

        t = Utils.get_model_type(type)
        if t is None:
            raise BadRequestException(detail="Invalid Model type")

        return t.select_me().count()

    # -- F --

    @classmethod
    def fetch_model(cls, type_str: str, uri: str) -> Model:
        """
        Fetch a model

        :param type: The type of the model
        :type type: `str`
        :param uri: The uri of the model
        :type uri: `str`
        :return: A model
        :rtype: instance of `gws.db.model.Model`
        """

        model_type: Type[Model] = Utils.get_model_type(type_str)
        if model_type is None:
            return None

        return model_type.get_by_uri_and_check(uri)

    @classmethod
    def fetch_list_of_models(cls,
                             type_str: str,
                             search_text: str = None,
                             page: int = 0, number_of_items_per_page: int = 20,
                             as_json: bool = False) -> Union[Paginator, List[Model], List[dict]]:

        t = Utils.get_model_type(type_str)
        if t is None:
            raise BadRequestException(detail="Invalid Model type")
        number_of_items_per_page = min(
            number_of_items_per_page, cls._number_of_items_per_page)
        if search_text:
            query = t.search(search_text)
            result = []
            for o in query:
                if as_json:
                    result.append(o.get_related().to_json())
                else:
                    result.append(o.get_related())
            paginator = Paginator(
                query, page=page, number_of_items_per_page=number_of_items_per_page)
            return {
                'data': result,
                'paginator': paginator._get_paginated_info()
            }
        else:
            query = t.select().order_by(t.creation_datetime.desc())
            paginator = Paginator(
                query, page=page, number_of_items_per_page=number_of_items_per_page)
            if as_json:
                return paginator.to_json()
            else:
                return paginator

    # -- G --

    @classmethod
    def get_model_types(cls):
        if not getattr(cls, '__model_types', None):
            cls.__model_types: List[Type[Model]] = Model.inheritors()

        return cls.__model_types

    @classmethod
    def get_db_and_model_types(cls, models: list = None) -> Tuple[DatabaseProxy, List[Type[Model]]]:
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

    # -- I --

    # -- R --

    @classmethod
    def register_all_processes_and_resources(cls) -> Dict[str, type]:
        TypingManager.save_object_types_in_db()

    # -- S --

    @classmethod
    @transaction()
    def save_all(cls, model_list: List[Model] = None) -> List[Model]:
        """
        Atomically and safely save a list of models in the database. If an error occurs
        during the operation, the whole transactions is rolled back.

        :param model_list: List of models
        :type model_list: `list`
        :return: True if all the model are successfully saved, False otherwise.
        :rtype: `bool`
        """

        if model_list is None:
            return
            #model_list = cls.models.values()

        # 1) save processes
        for model in model_list:
            if isinstance(model, ProcessModel):
                model.save()

        # 2) save resources
        for model in model_list:
            if isinstance(model, ResourceModel):
                model.save()

        # 3) save vmodels
        for model in model_list:
            if isinstance(model, ViewModel):
                model.save()

        return model_list

    @classmethod
    def __set_archive_status(cls, tf: bool, type: str, uri: str) -> dict:
        obj = cls.fetch_model(type, uri)
        if obj is None:
            raise NotFoundException(detail=f"Model not found with uri {uri}")
        obj.archive(tf)
        return obj

    # -- U --

    @classmethod
    def unarchive_model(cls, type: str, uri: str) -> dict:
        return cls.__set_archive_status(False, type, uri)

    # -- V --

    @classmethod
    def verify_model_hash(cls, type, uri) -> bool:
        """
        Verify model hash

        :param type: The type of the model
        :type type: `str`
        :param uri: The uri of the model
        :type uri: `str`
        :return: True if the hash is valid, False otherwise
        :rtype: `bool`
        """

        obj = cls.fetch_model(type, uri)
        if obj is None:
            raise NotFoundException(detail=f"Model not found with uri {uri}")
        return obj.verify_hash()  # {"status": obj.verify_hash()}

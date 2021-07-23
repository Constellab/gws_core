# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import importlib
import inspect
import os
from typing import Dict, List

from ..config import Config
from ..db.model import Model
from ..dto.rendering_dto import RenderingDTO
from ..experiment import Experiment
from ..http import *
from ..process import Process
from ..protocol import Protocol
from ..query import Paginator
from ..resource import Resource
from ..settings import Settings
from ..view_model import ViewModel
from .base_service import BaseService


class ModelService(BaseService):

    _model_types: Dict[str, type] = {}

    # -- A --

    @classmethod
    def archive_model(cls, type: str, uri: str) -> dict:
        return cls.__set_archive_status(True, type, uri)

    # -- C --

    @classmethod
    def create_view_model(cls, type: str, uri: str, data: RenderingDTO) -> (ViewModel,):
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

        t = cls.get_model_type(type)
        if t is None:
            raise HTTPNotFound(detail=f"Model type '{type}' not found")
        try:
            view_model = t.get(t.uri == uri).create_view_model(
                data=data.dict())
            return view_model
        except Exception as err:
            raise HTTPNotFound(
                detail=f"Cannot create a view_model for the model of type '{type}' and uri '{uri}'", debug_error=err) from err

    @classmethod
    def create_tables(cls, models: List[type] = None, model_type: type = None):
        """
        Create tables (if they don't exist)

        :param models: List of model tables to create
        :type models: `List[type]`
        :param instance: If provided, only the tables of the models that are instances of `model_type` will be create
        :type model_type: `type`
        """

        db_list, model_list = cls._get_db_and_model_lists(models)
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

        db_list, model_list = cls._get_db_and_model_lists(models)
        for db in db_list:
            try:
                i = db_list.index(db)
                models: List[Model] = [
                    t for t in model_list[i] if t.table_exists()]
                if model_type:
                    models = [t for t in models if isinstance(t, model_type)]
                if models[0].is_mysql_engine():
                    db.execute_sql("SET FOREIGN_KEY_CHECKS=0")
                db.drop_tables(models)
                if models[0].is_mysql_engine():
                    db.execute_sql("SET FOREIGN_KEY_CHECKS=1")
            except:
                pass

    @classmethod
    def count_model(cls, type: str) -> int:
        """
        Counts models
        """

        t = cls.get_model_type(type)
        if t is None:
            raise HTTPNotFound(detail=f"Invalid Model type")

        return t.select_me().count()

    # -- F --

    @classmethod
    def fetch_model(cls, type: str, uri: str, as_json=False) -> (Model,):
        """
        Fetch a model

        :param type: The type of the model
        :type type: `str`
        :param uri: The uri of the model
        :type uri: `str`
        :return: A model
        :rtype: instance of `gws.db.model.Model`
        """

        t = cls.get_model_type(type)
        if t is None:
            return None
        try:
            o = t.get(t.uri == uri)
            if as_json:
                o.to_json()
            else:
                return o
        except Exception as _:
            return None

    @classmethod
    def fetch_list_of_models(cls,
                             type: str,
                             search_text: str = None,
                             page: int = 1, number_of_items_per_page: int = 20,
                             as_json: bool = False) -> (Paginator, List[Model], List[dict]):

        t = cls.get_model_type(type)
        if t is None:
            raise HTTPNotFound(detail=f"Invalid Model type")
        number_of_items_per_page = min(
            number_of_items_per_page, cls._number_of_items_per_page)
        if search_text:
            query = t.search(search_text)
            result = []
            for o in query:
                if as_json:
                    result.append(o.get_related().to_json(shallow=True))
                else:
                    result.append(o.get_related())
            paginator = Paginator(
                query, page=page, number_of_items_per_page=number_of_items_per_page)
            return {
                'data': result,
                'paginator': paginator._paginator_dict()
            }
        else:
            query = t.select().order_by(t.creation_datetime.desc())
            paginator = Paginator(
                query, page=page, number_of_items_per_page=number_of_items_per_page)
            if as_json:
                return paginator.to_json(shallow=True)
            else:
                return paginator

    # -- G --

    @classmethod
    def _get_db_and_model_lists(cls, models: list = None):
        if not models:
            models = ModelService._inspect_model_types()
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

    @classmethod
    def get_model_types(cls) -> Dict[str, type]:
        if not cls._model_types:
            cls.register_all_processes_and_resources()
        return cls._model_types

    @classmethod
    def get_model_type(cls, type: str = None) -> type:
        """
        Get the type of a registered model using its litteral type

        :param type: Litteral type (can be a slugyfied string)
        :type type: str
        :return: The type if the model is registered, None otherwise
        :type: `str`
        """

        if type is None:
            return None
        if type in cls._model_types:
            return cls._model_types[type]

        if type.lower() == "experiment":
            return Experiment
        elif type.lower() == "protocol":
            return Protocol
        elif type.lower() == "process":
            return Process
        elif type.lower() == "resource":
            return Resource
        elif type.lower() == "config":
            return Config

        tab = type.split(".")
        n = len(tab)
        module_name = ".".join(tab[0:n-1])
        function_name = tab[n-1]
        try:
            module = importlib.import_module(module_name)
            t = getattr(module, function_name, None)
            cls._model_types[type] = t
        except Exception as err:
            Logger.warning(
                f"gws.service.model_service.ModelService get_model_type An error occured. Error: {err}")
            t = None

        return t

    # -- I --

    @classmethod
    def _inspect_model_types(cls):
        settings = Settings.retrieve()
        dep_dirs = settings.get_dependency_dirs()

        def __get_list_of_sub_modules(cdir):
            modules = [[f, dirpath]
                       for dirpath, dirnames, files in os.walk(cdir)
                       for f in files if f.endswith('.py') and not f.startswith('_')
                       ]

            f = []
            for kv in modules:
                file_name = kv[0]
                folder = kv[1].replace(cdir, '').replace("/", ".").strip(".")
                file_name = file_name.replace(".py", "")
                if "._" in folder or folder.startswith("_"):
                    continue

                if folder:
                    f.append(folder+"."+file_name)
                else:
                    f.append(file_name)

            return f

        model_type_list = []
        for brick_name in dep_dirs:
            cdir = dep_dirs[brick_name]
            module_names = __get_list_of_sub_modules(
                os.path.join(cdir, brick_name))
            if brick_name == "gws":
                _black_list = ["settings", "runner", "manage", "logger"]
                for k in _black_list:
                    try:
                        module_names.remove(k)
                    except Exception as _:
                        pass
            for module_name in module_names:
                try:
                    submodule = importlib.import_module(
                        brick_name+"."+module_name)
                    for class_name, _ in inspect.getmembers(submodule, inspect.isclass):
                        t = getattr(submodule, class_name, None)
                        if issubclass(t, Model):
                            model_type_list.append(t)
                except Exception as _:
                    pass
        model_type_list = list(set(model_type_list))
        return model_type_list

    # -- R --

    @classmethod
    def register_all_processes_and_resources(cls):
        model_type_list = cls._inspect_model_types()
        process_type_list = []
        resource_type_list = []
        for m_t in set(model_type_list):
            if issubclass(m_t, Process):
                process_type_list.append(m_t)
                if (not m_t is Process) and (not m_t is Protocol):
                    m_t.create_process_type()
                    cls._model_types[m_t.full_classname()] = m_t
            elif issubclass(m_t, Resource):
                resource_type_list.append(m_t)
                if not m_t is Resource:
                    m_t.create_resource_type()
                    cls._model_types[m_t.full_classname()] = m_t
        Logger.info(
            f"Resource: {len(resource_type_list)} types registered:\n{resource_type_list}")
        Logger.info(
            f"Process: {len(process_type_list)} types registered:\n{process_type_list}")

    # -- S --

    @classmethod
    def save_all(cls, model_list: List[Model] = None) -> bool:
        """
        Atomically and safely save a list of models in the database. If an error occurs
        during the operation, the whole transactions is rolled back.

        :param model_list: List of models
        :type model_list: `list`
        :return: True if all the model are successfully saved, False otherwise.
        :rtype: `bool`
        """

        with Model.get_db_manager().db.atomic() as transaction:
            try:
                if model_list is None:
                    return
                    #model_list = cls.models.values()

                # 1) save processes
                for model in model_list:
                    if isinstance(model, Process):
                        model.save()

                # 2) save resources
                for model in model_list:
                    if isinstance(model, Resource):
                        model.save()

                # 3) save vmodels
                for model in model_list:
                    if isinstance(model, ViewModel):
                        model.save()
            except Exception as _:
                transaction.rollback()
                return False

        return True

    @classmethod
    def __set_archive_status(cls, tf: bool, type: str, uri: str) -> dict:
        obj = cls.fetch_model(type, uri)
        if obj is None:
            raise HTTPNotFound(detail=f"Model not found with uri {uri}")
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
            raise HTTPNotFound(detail=f"Model not found with uri {uri}")
        return obj.verify_hash()  # {"status": obj.verify_hash()}

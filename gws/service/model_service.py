# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import glob
import os
import importlib
import inspect

from typing import List
from gws.query import Paginator
from gws.model import Model, ViewModel, Process, Resource, Protocol, Experiment, Config
from gws.settings import Settings
from gws.logger import Warning, Info, Error
from gws.http import *
from gws.dto.rendering_dto import RenderingDTO

from .base_service import BaseService

class ModelService(BaseService):
    
    _model_types = {}
    
    # -- A --
    
    @classmethod
    def archive_model(cls, type: str, uri: str) -> dict:
        return cls.__set_archive_status(True, type, uri)
    
    # -- C --
    
    @classmethod
    def creat_view_model(cls, type: str, uri: str, data: RenderingDTO) -> (ViewModel,):
        """
        View a model

        :param type: The type of the model
        :type type: `str`
        :param uri: The uri of the model
        :type uri: `str`
        :param data: The rendering data
        :type data: `dict`
        :return: A model if `as_json == False`, a dictionary if `as_json == True=
        :rtype: `gws.model.Model`, `dict`
        """

        t = cls.get_model_type(type)
        
        if t is None:
            raise HTTPNotFound(detail=f"Model type '{type}' not found")
        
        try:
            vm = t.get(t.uri == uri).create_view_model(data=data.dict())
            return vm
        except Exception as err:
            raise HTTPNotFound(detail=f"Cannot create a view_model for the model of type '{type}' and uri '{uri}'", debug_error=err) from err

            
    @classmethod
    def create_model_tables(cls):
        """
        Create all model tables
        """
        
        for k in cls._model_types:
            t = cls._model_types[k]
            if not t.table_exists():
                t.create_table()
                
    @classmethod
    def count_model(cls, type: str) -> int:
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
        :rtype: instance of `gws.model.Model`
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
        except:
            return None
    
    @classmethod
    def fetch_list_of_models(cls, \
                             type: str,  \
                             search_text: str=None, \
                             page:int=1, number_of_items_per_page: int=20, \
                             as_json: bool=False) -> (Paginator, List[Model], List[dict]):
        
        t = cls.get_model_type(type)
        if t is None:
            raise HTTPNotFound(detail=f"Invalid Model type")
        
        number_of_items_per_page = min(number_of_items_per_page, cls._number_of_items_per_page)
        
        if search_text:
            query = t.search(search_text)
            result = []
            for o in query:
                if as_json:
                    result.append(o.get_related().to_json(shallow=True))
                else:
                    result.append(o.get_related())
            
            paginator = Paginator(query, page=page, number_of_items_per_page=number_of_items_per_page)
            return {
                'data' : result,
                'paginator': paginator._paginator_dict()
            }
        else:
            query = t.select().order_by(t.creation_datetime.desc())
            paginator = Paginator(query, page=page, number_of_items_per_page=number_of_items_per_page)
            
            if as_json:
                return paginator.to_json(shallow=True)
            else:
                return paginator
 
    # -- G --
    
    @classmethod
    def get_model_types(cls) -> List[type]:
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
            Warning("gws.service.model_service.ModelService", "get_model_type", f"An error occured. Error: {err}")
            t = None

        return t
    
    # -- R --
    
        
    @classmethod
    def register_all_processes_and_resources(cls):
        settings = Settings.retrieve()
        dep_dirs = settings.get_dependency_dirs()
        
        def __get_list_of_sub_modules(cdir):
            modules = glob.glob(os.path.join(cdir, "*.py"))
            return [ os.path.basename(f)[:-3] for f in modules if os.path.isfile(f) and not f.startswith('_')]

        resource_type_list = []
        process_type_list = []
        
        for brick_name in dep_dirs:
            cdir = dep_dirs[brick_name]
            module_names = __get_list_of_sub_modules( os.path.join(cdir, brick_name) )
  
            if brick_name == "gws":
                _black_list = ["settings", "runner", "manage", "logger"]
                for k in _black_list:
                    try:
                        module_names.remove(k)
                    except:
                        pass

            for module_name in module_names:
                try:
                    submodule = importlib.import_module(brick_name+"."+module_name)
                    for class_name, _ in inspect.getmembers(submodule, inspect.isclass):
                        t = getattr(submodule, class_name, None)
                        if issubclass(t, Process):
                            process_type_list.append(t)
                        elif issubclass(t, Resource):
                            resource_type_list.append(t)
                except:
                    pass
        
        process_type_list = list(set(process_type_list))
        for proc_t in set(process_type_list):
            if not proc_t is Process and not proc_t is Protocol:
                proc_t.create_process_type()
                cls._model_types[ proc_t.full_classname() ] = proc_t
            
        resource_type_list = list(set(resource_type_list))
        for res_t in set(resource_type_list):
            if not res_t is Resource:
                res_t.create_resource_type()
                cls._model_types[ res_t.full_classname() ] = res_t
            
        Info(f"REGISTER_ALL_PROCESSES: A total of {len(process_type_list)} process types were registered in db.\n Process types:\n {process_type_list}")
        
        Info(f"REGISTER_ALL_RESOURCES: A total of {len(resource_type_list)} resource types were registered in db.\n Resource types:\n {resource_type_list}")
        
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

        with Model._db_manager.db.atomic() as transaction:
            try:
                if model_list is None:
                    return
                    #model_list = cls.models.values()
                
                # 1) save processes
                for m in model_list:
                    if isinstance(m, Process):
                        m.save()
                
                # 2) save resources
                for m in model_list:
                    if isinstance(m, Resource):
                        m.save()

                # 3) save vmodels
                for m in model_list:
                    if isinstance(m, ViewModel):
                        m.save()
            except:
                transaction.rollback()
                return False

        return True
    
    @classmethod
    def __set_archive_status(cls, tf:bool, type: str, uri: str) -> dict:
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
        
        return obj.verify_hash() #{"status": obj.verify_hash()}
    

    
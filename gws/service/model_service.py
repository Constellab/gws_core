# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import glob
import os
import importlib
import inspect

from typing import List
from gws.base import DbManager
from gws.query import Paginator
from gws.model import Model, ViewModel, Process, Resource, Protocol, Experiment
from gws.settings import Settings
from gws.logger import Warning, Info, Error
from gws.http import *

from .base_service import BaseService

class ModelService(BaseService):
    
    _model_types = {}
    
    # -- A --
    
    @classmethod
    def archive_model(cls, object_type: str, object_uri: str) -> ViewModel:
        return cls.__set_archive_status(True, object_type, object_uri)
    
    # -- C --
    
    @classmethod
    def count_model(cls, object_type: str) -> int:
        t = cls.get_model_type(object_type)
        if t is None:
            raise HTTPNotFound(detail=f"Invalid Model type")

        return t.select_me().count()

    
    # -- F --
    
    @classmethod
    def fetch_model(cls, object_type: str, object_uri: str) -> Model:
        """
        Fetch a model

        :param object_type: The type of the model
        :type object_type: `str`
        :param object_uri: The uri of the model
        :type object_uri: `str`
        :return: A model
        :rtype: instance of `gws.model.Model`
        """

        t = cls.get_model_type(object_type)
        
        if t is None:
            return None
        
        try:
            return t.get(t.uri == object_uri)
        except:
            return None   
   
    @classmethod
    def fetch_view_model(cls, object_type: str, object_uri: str, data:dict=None) -> ViewModel:
        """
        Fetch a view model

        :param object_type: The type of the model to view
        :type object_type: `str`
        :param object_uri: The uri of the model
        :type object_uri: `str`
        :return: A model
        :rtype: instance of `gws.model.ViewModel`
        """
        
        obj = cls.fetch_model(object_type, object_uri)
        if obj is None:
            raise HTTPNotFound(detail=f"Invalid Model type or uri not found")
        
        if isinstance(obj, ViewModel):
            # Ok!
            pass
        elif isinstance(obj, Model):
            obj = obj.view(params=data)  
        else:
            raise HTTPNotFound(detail=f"No Model found with uri {object_uri}")
        
        return obj.to_json()
    
    @classmethod
    def fetch_list_of_view_models(cls, object_type: str, object_uris: List[str],  data:dict=None, filters: str=None, page=1, number_of_items_per_page=20) -> list:
        t = cls.get_model_type(object_type)
        
        if t is None:
            raise HTTPNotFound(detail=f"Invalid Model type")
        
        number_of_items_per_page = min(number_of_items_per_page, cls._number_of_items_per_page)
        
        if "all" in object_uris:
            if filters:
                Q = t.search(**filters)

                p = Paginator(Q, page=page, number_of_items_per_page=number_of_items_per_page, view_params=data)
                result = []
                for o in p:
                    if return_format=="json":
                        result.append( o.get_related().to_json(shallow=True) )
                    else:
                        result.append(o)

                return {
                    'data' : result,
                    'paginator': p._paginator_dict()
                }
            else:
                Q = t.select().order_by(t.creation_datetime.desc())
                return Paginator(Q, page=page, number_of_items_per_page=number_of_items_per_page, view_params=data).to_json(shallow=True)
        else:
            Q = t.select().where(t.uri.in_(object_uris)).order_by(t.creation_datetime.desc())
            return Paginator(Q, page=page, number_of_items_per_page=number_of_items_per_page, view_params=data).to_json(shallow=True)
        
    # -- G --
    
    @classmethod
    def get_model_type(cls, type_str: str = None) -> type:
        """
        Get the type of a registered model using its litteral type
        
        :param type_str: Litteral type (can be a slugyfied string)
        :type type_str: str
        :return: The type if the model is registered, None otherwise
        :object_type: type
        """
   
        if type_str is None:
            return None
        
        if type_str in cls._model_types:
            return cls._model_types[type_str]
        
        if type_str.lower() == "experiment":
            return Experiment
        elif type_str.lower() == "protocol":
            return Protocol
        elif type_str.lower() == "process":
            return Process
        elif type_str.lower() == "resource":
            return Resource
        elif type_str.lower() == "config":
            return Config
 
        tab = type_str.split(".")
        n = len(tab)
        module_name = ".".join(tab[0:n-1])
        function_name = tab[n-1]
        
        try:
            module = importlib.import_module(module_name)
            t = getattr(module, function_name, None)
            cls._model_types[type_str] = t
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
            return [ os.path.basename(f)[:-3] for f in modules if os.path.isfile(f) and not f.endswith('__init__.py')]

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
            proc_t.create_process_type()
            cls._model_types[ proc_t.full_classname() ] = proc_t
            
        
        resource_type_list = list(set(resource_type_list))
        for res_t in set(resource_type_list):
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
        
        with DbManager.db.atomic() as transaction:
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
    def __set_archive_status(cls, tf:bool, object_type: str, object_uri: str) -> ViewModel:
        obj = cls.fetch_model(object_type, object_uri)
        
        if obj is None:
            raise HTTPNotFound(detail=f"Model not found with uri {object_uri}")

        obj.archive(tf)
        return obj.to_json()
            
    # -- U --
    
    @classmethod
    def unarchive_model(cls, object_type: str, object_uri: str) -> ViewModel:
        return cls.__set_archive_status(False, object_type, object_uri)
    
    @classmethod
    def update_view_model(cls, object_type: str, object_uri: str, data: dict) -> ViewModel:
        obj = cls.fetch_model(object_type, object_uri)
        if obj is None:
            raise HTTPNotFound(detail=f"Model not found with uri {object_uri}")
        
        if isinstance(obj, ViewModel):
            view_model = obj
            view_model.set_params(data)
            view_model.save()
        else:
            raise HTTPNotFound(detail=f"ViewModel not found with uri {object_uri}")

        return view_model.to_json()
    
    # -- V --
    
    @classmethod
    def verify_model_hash(cls, object_type, object_uri):
        obj = cls.fetch_model(object_type, object_uri)
        if obj is None:
            raise HTTPNotFound(detail=f"Model not found with uri {object_uri}")
        
        return {"status": obj.verify_hash()}
    
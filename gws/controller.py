# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import asyncio
import json
import importlib

from gws.base import Base
from gws.logger import Logger

class Controller(Base):
    """
    Controller class
    """

    _model_specs = dict() 

    @classmethod
    def action(cls, action=None, rtype=None, uri=None, data=None) -> 'ViewModel':
        """
        Process user actions

        :param action: The action
        :type action: str
        :param encoded_uri: The uri of the view model
        :type encoded_uri: str
        :param data: The data
        :type data: dict
        :return: A view model corresponding to the action
        :rtype: `gws.prims.model.ViewModel`
        """

        try:
            if isinstance(data, str):
                if len(data) == 0:
                    data = {}
                else:
                    data = json.loads(data)
        except:
            Logger.error(Exception("Controller", "action", "The data is not a valid JSON text"))
        
        # CRUD (& Run) actions
        if action == "post":
            return cls.__post(rtype, uri, data)

        elif action == "get":
            return cls.__get(rtype, uri)

        elif action == "put":
            return cls.__put(rtype, uri, data)

        elif action == "delete":
            return cls.__delete(rtype, uri)

        elif action == "run":
            return cls.__run(rtype, uri, data)

    # -- C --

    # -- D --

    @classmethod
    def __delete(cls, rtype: str, uri: str) -> 'ViewModel':
        from gws.model import Model, ViewModel
        o = cls.fetch_model(rtype, uri)
        if isinstance(o, ViewModel):
            o.delete()
            return o
        else:
            Logger.error(Exception("Controller", f"__delete", "No ViewModel match with the uri."))

    # -- F --

    @classmethod
    def fetch_model(cls, rtype: str, uri: str) -> 'Model':
        """
        Fetch a model using the encoded_uri

        :param encoded_uri: The uri of the target model
        :type encoded_uri: str
        :return: A model
        :rtype: Model
        """

        t = cls.get_model_type(rtype)
        try:
            return t.get(t.uri == uri)
        except:
            return None        
    # -- G --

    @classmethod
    def __get(cls, rtype: str, uri: str) -> 'ViewModel':
        obj = cls.fetch_model(rtype, uri)
        from gws.model import ViewModel
        if isinstance(obj, ViewModel):
            vmodel = obj
        else:
            Logger.error(Exception("Controller", "__get", f"No ViewModel found for the encoded uri {encoded_uri}"))
        return vmodel

    @classmethod
    def get_model_type(cls, type_str: str) -> type:
        """
        Get the type of a registered model using its litteral type
        
        :param type_str: Litteral type (can be a slugyfied string)
        :type type_str: str
        :return: The type if the model is registered, None otherwise
        :rtype: type
        :Logger.error(Exception: No registered model matchs with the given `type_str`)
        """
   
        if type_str is None:
            return None
            
        tab = type_str.split(".")
        n = len(tab)
        module_name = ".".join(tab[0:n-1])
        function_name = tab[n-1]
        module = importlib.import_module(module_name)
        t = getattr(module, function_name, None)
        if t is None:
            Logger.error(Exception(f"Cannot import {type_str}"))
        return t

    # -- I --

    # -- P --

    @classmethod
    def __post(cls, rtype: str, uri: str, data: dict) -> 'ViewModel':
        from gws.model import SystemTrackable, ViewModel
        obj = cls.fetch_model(rtype, uri)

        if isinstance(obj, SystemTrackable):
            Logger.error(Exception("Controller", "__post", f"Object {type(obj)} is SystemTrackable. It can only be created by the PRISM system"))

        if isinstance(obj, ViewModel):
            vmodel = cls.__post_new_vmodel(obj, data)
        else:
            Logger.error(Exception("Controller", "__post", f"Object {type(obj)} is not a ViewModel"))
        
        return vmodel
    
    @classmethod
    def __post_new_vmodel(cls, vmodel, data):
        if data["type"] == "self":
            vmodel_t = type(vmodel)
        else:
            vmodel_t = cls.get_model_type(data["type"])

        new_vmodel = vmodel_t(model=vmodel.model)
        vdata = data.get("vdata", {})
        new_vmodel.hydrate_with(vdata)
        new_vmodel.save()
        return new_vmodel

    @classmethod
    def __post_new_model_and_return_vmodel(cls, rtype: str, uri: str, data: dict):
        model_t = cls.get_model_type(rtype)
        model = model_t()

        from gws.model import Model
        if not isinstance(model, Model):
            Logger.error(Exception("Controller", "action", "The action uri must refer to a Model"))

        mdata = data.get("mdata", {})
        model.hydrate_with(mdata)

        vmodel = model.create_default_vmodel()
        vdata = data.get("vdata", {})
        vmodel.hydrate_with(vdata)
        vmodel.save()

        return vmodel

    @classmethod
    def __put(cls, rtype: str, uri: str, data: dict) -> 'ViewModel':
        from gws.model import SystemTrackable, ViewModel
        t = cls.get_model_type(rtype)
        
        try:
            obj = t.get(t.uri == uri)
        except:
            Logger.error(Exception("Controller", "__post", f"Object {type(obj)} is not found with uri {uri}"))

        if isinstance(obj, SystemTrackable):
            Logger.error(Exception("Controller", "__post", f"Object {type(obj)} is SystemTrackable. It can only be updated by the PRISM system"))

        if isinstance(obj, ViewModel):
            vmodel = obj

            model = vmodel.model
            mdata = data.get("mdata", {})
            model.hydrate_with(mdata)

            vdata = data.get("vdata", {})
            vmodel.hydrate_with(vdata)
            vmodel.save()
        else:
            # it is a model
            model = obj
            mdata = data.get("mdata", {})
            model.hydrate_with(mdata)

            vmodel = model.create_default_vmodel()
            vdata = data.get("vdata", {})
            vmodel.hydrate_with(vdata)
            vmodel.save()

        return vmodel

    # -- R --

    @classmethod
    def __run(cls, rtype: str, uri: str, data: dict):
        t = cls.get_model_type(rtype)
        obj = t()
        obj.data = data

        from gws.model import Process
        import asyncio 
        if isinstance(obj, Process):
            asyncio.run( obj.run() )
        else:
            Logger.error(Exception("Controller", "__run", "Only processes can be run"))

    @classmethod
    def save_all(cls, model_list: list = None) -> bool:
        """
        Atomically and safely save a list of models in the database. If an error occurs
        during the operation, the whole transactions is rolled back.
        
        :param model_list: List of models
        :type model_list: list
        :return: True if all the model are successfully saved, False otherwise. 
        :rtype: bool
        """
        from gws.base import DbManager
        from gws.model import Process, Resource, ViewModel
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

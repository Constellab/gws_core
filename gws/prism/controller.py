# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import asyncio
import json
from gws.prism.base import Base
from gws.prism.base import slugify
from gws.logger import Logger
from gws.session import Session

class Controller(Base):
    """
    Controller class
    """

    _model_specs = dict()    
    is_query_params = False
    
    @classmethod
    async def action(cls, request: 'Request') -> 'ViewModel':
        """
        Process user actions
        :param request: Starlette request
        :type request: `starlette.requests.Request`
        :return: A view model corresponding to the action
        :rtype: `gws.prims.model.ViewModel`
        """

        #cls._session = request.session
        cls.__inspects()

        if Controller.is_query_params:
            action = request.query_params.get('action','')
            uri = request.query_params.get('uri','')
            params = request.query_params.get('params','{}')
        else:
            action = request.path_params.get('action','')
            uri = request.path_params.get('uri','')
            params = request.path_params.get('params','{}')

        try:
            if len(params) == 0:
                params = {}
            else:
                params = json.loads(params)
        except:
            Logger.error(Exception("Controller", "action", "The params is not a valid JSON text"))

        return cls._do_action(action, uri, params)
    
    @classmethod
    def _do_action(cls, action: str, uri: str, params: dict) -> 'ViewModel':
        """
        Process user actions
        :param action: Action name.
            Accpeted values are 'view' to render a ViewModel or 'run' to launch a Process
        :type action: str
        :param uri: The uri of the target ViewModel or Process 
        :type uri: str
        :param params: The action parameters (JSON dictionnary)
            Accepted keys,values are:
            * 'target': uri_name of the target ViewModel, Defaults to 'self'
                * `None` or 'self' to deal with the current ViewModel represented by the uri or 
                * The name of a new ViewModel to generate.
            * 'params': The parameter data
        :type params: dict
        :return: A view model corresponding to the action
        :rtype: `gws.prims.model.ViewModel`
        """
      
        view_model = cls.fetch_model(uri)

        from gws.prism.model import ViewModel
        if not isinstance(view_model, ViewModel):
            Logger.error(Exception("Controller", "action", "The action uri must target a ViewModel"))
        
        if action == "view":
            target = params.get("target",None)
            params = params.get("params",{})

            if target is None or target == "self":
                # OK!
                # simply load the current ViewModel with the new parameters
                pass
            else:
                # generate a new ViewModel
                view_model = view_model.model.create_view_model_by_name(target)
                if not isinstance(view_model, ViewModel):
                    Logger.error(Exception("Controller", "action", "The view model '"+ target+"' cannot ne created."))
         
                view_model.set_data(params)
                view_model.save()
        
            view_model.set_data(params)
        elif action == "run":
            # run a Process and render its default ViewModel
            pass
        else:
            pass # OK!
        
        return view_model

    # -- B --

    @classmethod
    def build_url(cls, action: str = None, uri: str = None, params: dict = None) -> str:
        """
        Build the url of action using the action name, the target model uri and request parameters
        :param action: User action
        :type action: str
        :param uri: The uri of the target model
        :type uri: str
        :param params: Action parameters
        :type params: dict
        :return: A view model corresponding to the action
        :rtype: `gws.prims.model.ViewModel`
        """        
        if Controller.is_query_params:
            return '/?action='+action+'&uri='+uri+'&params=' + str(params)
        else:
            return '/'+action+'/'+uri+'/'+str(params)

    # -- F --

    @classmethod
    def fetch_model(cls, uri: str) -> 'Model':
        """
        Fetch a model using its uri
        :param uri: The uri of the target model
        :type uri: str
        :return: A model
        :rtype: `gws.prims.model.Model`
        """
        from gws.prism.model import Model
        tab = Model.parse_uri(uri)
        return cls.fetch_model_by_uri_name_id(tab[0], tab[1])

    @classmethod
    def fetch_model_by_uri_name_id(cls, uri_name: str, uri_id: str) -> 'Model':
        """
        Fetch a model from db using its uri_name and uri_id
        :param uri_name: The uri_name of the target model
        :type uri_name: str
        :param uri_id: The uri_id of the target model
        :type uri_id: str
        :return: A model
        :rtype: `gws.prims.model.Model`
        """

        model_t = cls.get_model_type(uri_name)
        Q = model_t.select().where(
            model_t.id == uri_id, 
            model_t.type == model_t.full_classname()
        )
        
        if len(Q) == 1:
            return Q[0]
        elif len(Q) == 0:
            Logger.error(Exception("Controller", "action", "No model matchs with the request: (uri_name={uri_name}, uri_id={uri_id})"))
        else:
            Logger.error(Exception("Controller", f"action", "Db integrity error. Several models match with the request: (uri_name={uri_name}, uri_id={uri_id})"))
        
    # -- G --

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
        cls.__inspects()

        type_str = slugify(type_str)
        if type_str in cls._model_specs:
            return cls._model_specs[type_str]
        else:
            Logger.error(Exception("Controller", "get_model_type", f"No registered model matchs with '{type_str}'"))

    # -- I --

    @classmethod
    def __inspects(cls):
        if len(cls._model_specs):
            return

        from gws.settings import Settings
        settings = Settings.retrieve()
        module_names = settings.get_dependency_names()
 
        for k in module_names:
            cls.__inspects_module(k)
        
        cls.__inspects_module('tests')  #for testing

    @classmethod
    def __inspects_module(cls, name):
        import inspect
        import sys
        from gws.prism.model import Model, ViewModel, HTMLViewModel, JSONViewModel
        if not name in sys.modules:
            return

        for subname, obj in inspect.getmembers(sys.modules[name]):
            #print(subname)
            if inspect.isclass(obj):
                if issubclass(obj, Model):
                    cls._register_model_specs([ obj ])
                    # register the ViewModel to the default Model
                    if issubclass(obj, ViewModel):
                        obj.register_to_models()

            elif inspect.ismodule(obj):
                cls.__inspects_module(name+"."+subname)

    # -- R --

    @classmethod
    def _register_model_specs(cls, model_specs: list):
        """
        Register Models. 
        
        Only Models of which types are registered will be actionable.
        Override the names of the model tables.

        :param model_specs: List of Model types to regiters
        :type model_specs: list
        """
        for model_type in model_specs:
            if isinstance(model_type, type):
                full_cname = model_type.full_classname(slugify=True)
                cls._model_specs[full_cname] = model_type
                #model_type._meta.table_name = model_type._table_name
            else:
                Logger.error(Exception("Controller", "_register_model_specs", "Invalid model type"))

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
        from gws.prism.base import DbManager
        from gws.prism.model import Process, Resource, ViewModel
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

                # 3) save view_models
                for m in model_list:
                    if isinstance(m, ViewModel):
                        m.save()
            except:
                transaction.rollback()
                return False

        return True
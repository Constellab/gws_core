# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import asyncio
import json
from gws.prism.base import Base

class Controller(Base):
    """
    Controller class
    """

    #models = dict()
    model_specs = dict()
    is_query_params = False
    
    @classmethod
    async def action(cls, request: 'Request') -> 'ViewModel':
        """
        Asynchronously process user actions
        :param request: Starlette request
        :type request: `starlette.requests.Request`
        :return: A view model corresponding to the action
        :rtype: `gws.prims.model.ViewModel`
        """
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
            raise Exception("Controller", "action", "The params is not a valid JSON text")
        
        view_model = cls.fetch_model(uri)

        from gws.prism.model import ViewModel
        if not isinstance(view_model, ViewModel):
            raise Exception("Controller", "action", "The action uri must target a ViewModel")
         
        if action == "view":
            if params.get("view", None):
                # generate a new view model
                name = params["view"]
                params = params["params"]
                view_model = view_model.model.create_view_model_by_name(name)
                if not isinstance(view_model, ViewModel):
                    raise Exception("Controller", "action", "The the view '"+ name+"' cannot ne created.")
         
                view_model.set_data(params)
                view_model.save()
            else:
                # OK!
                # simply loads the current view with the new parameters
                pass
        
            view_model.set_data(params)
        elif action == "run":
            #run a process and render its view
            pass
        else:
            pass # OK!
        
        return view_model

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

    @classmethod
    def fetch_model(cls, uri: str) -> 'Model':
        """
        Fetch a model using its uri
        :param uri: The uri_name of the target model
        :type uri: str
        :return: A model
        :rtype: `gws.prims.model.Model`
        """
        from gws.prism.model import Model
        tab = Model.parse_uri(uri)
        print("--------")
        print(uri)
        print(tab)
        return cls.fetch_model_by_uri_name_id(tab[0], tab[1])

    @classmethod
    def fetch_model_by_uri_name_id(cls, uri_name: str, uri_id: str) -> 'Model':
        """
        Fetch a model using its uri_name and uri_id
        :param uri_name: The uri_name of the target model
        :type uri_name: str
        :param uri_id: The uri_id of the target model
        :type uri_id: str
        :return: A model
        :rtype: `gws.prims.model.Model`
        """
        model_class = cls.model_specs[uri_name]
        Q = model_class.select().where(
            model_class.id == uri_id, 
            model_class.type == model_class.full_classname()
        )
        
        if len(Q) == 1:
            return Q[0]
        elif len(Q) == 0:
            raise Exception("Controller", "action", "No model matchs with the request")
        else:
            raise Exception("Controller", "action", "Several models match with the request")

    @classmethod
    def register_model_specs(cls, model_specs: list):
        """
        Register Model types. Only Model instances of registered Model types are actionable, i.e. 
        can controlled by the Controller through :meth:`Controller.action`
        :param model_specs: List of Model types to regiters
        :type model_specs: list
        """
        for model_type in model_specs:
            if isinstance(model_type, type):
                full_cname = model_type.full_classname(slugify=True)
                cls.model_specs[full_cname] = model_type
                model_type._meta.table_name = model_type._table_name
            else:
                raise Exception("Controller", "register_model_specs", "Invalid model type")

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
        from gws.prism.model import DbManager, Process, Resource, ViewModel
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
  
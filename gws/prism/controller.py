#
# Python GWS view
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
#

import asyncio
import json
from gws.prism.base import Base

class Controller(Base):
    models = dict()
    model_specs = dict()
    is_query_params = False

    @classmethod
    async def action(cls, request: 'Request') -> 'ViewModel':
        """
            Deal with user actions
            Receive a request through a request url
            * url = /{action}/{uri_name}/{uri_id}/{params}
                * action:
                    - update_view:  to update the current active view
                    - create_view:  to create a new view using params
                    - run_proc:     to run the current process and return the result view
                * uri_name: 
                    - the name of the targeted resource
                * uri_id: 
                    - the id of the targeted resource
                * params: parameter ins JSON format    
                    e.g.:

                    update_view_params = {
                        ...
                    } 
                    
                    create_view_params = {
                        "view": "<unique.name.of.the.new.view.to.create>",
                        ...
                    } 

                    run_proc_params = {
                        "name": "<unique.name.of.the.process.to.run>",
                        "input":{
                            "resource_id": "<resource.id>",
                            "resource_type": "<resource.type>"
                        }
                    } 
        """

        if Controller.is_query_params:
            action = request.query_params.get('action','')
            uri_id = request.query_params.get('uri_id','')
            uri_name = request.query_params.get('uri_name','')
            params = request.query_params.get('params','{}')
        else:
            action = request.path_params.get('action','')
            uri_id = request.path_params.get('uri_id','')
            uri_name = request.path_params.get('uri_name','')
            params = request.path_params.get('params','{}')

        try:
            params = json.loads(params)
        except:
            raise Exception("Controller", "action", "The params is not a valid JSON text")

        view_model = cls.fetch_model_by_uri_name_id(uri_name, uri_id)

        from gws.prism.model import Model, ViewModel
        if not isinstance(view_model, ViewModel):
            raise Exception("Controller", "action", "The action uri must target a ViewModel.")

        if action == "update_view":
            view_model.set_data(params)
        elif action == "create_view":
            if view_model is None:
                raise Exception("Controller", "action", "It seems that this request comes form an undefined view")
            else:
                view_name = params["view"]
                params = params["params"]
                view_model = view_model.model.create_view_model_by_name(view_name)
                view_model.set_data(params)
        elif action == "run":
            #run a process and render its view
            pass
        else:
            pass # OK!
        
        # ensure that all models are saved
        Controller.save_all()   
        return view_model

    @classmethod
    def build_url(cls, action = None, uri_name = None, uri_id = None, params = None):
        if Controller.is_query_params:
            return '/?action='+action+'&uri_name='+uri_name+'&uri_id='+str(uri_id)+'&params=' + str(params)
        else:
            return '/'+action+'/'+uri_name+'/'+str(uri_id)+'/' + str(params)

    @classmethod
    def fetch_model_by_uri_name_id(cls, uri_name: str, uri_id: str) -> 'Model':
        model_class = cls.model_specs[uri_name]
        return model_class.get_by_id(uri_id)

    @classmethod
    def fetch_model(cls, uri: str) -> 'Model':
        from gws.prism.model import Model
        tab = Model.parse_uri(uri)
        return cls.fetch_model_by_uri_name_id(tab[0], tab[1])

    @classmethod
    def reset(cls):
        cls.models.clear()

    @classmethod
    def _register_model_instances(cls, models: list):
        from gws.prism.model import Model
        for model in models:
            if isinstance(model, Model):
                cls.models[model._uuid] = model
            else:
                raise Exception("Controller", "register_models", "Invalid model")

    @classmethod
    def register_models(cls, model_specs: list):
        """
            Uniquely register the model type
        """
        from gws.prism.model import Resource, Process, ResourceViewModel, ProcessViewModel, ViewModel
        for model_type in model_specs:
            if isinstance(model_type, type):
                full_cname = model_type.full_classname(slugify=True)
                cls.model_specs[full_cname] = model_type

                # change names of the tables of instances of prism objects
                if( issubclass(model_type, Resource) ):
                    model_type._meta.table_name = Resource._table_name
                elif( issubclass(model_type, Process) ):
                    model_type._meta.table_name = Process._table_name
                elif( issubclass(model_type, ResourceViewModel) ):
                    model_type._meta.table_name = ResourceViewModel._table_name
                elif( issubclass(model_type, ProcessViewModel) ):
                    model_type._meta.table_name = ProcessViewModel._table_name
                
            else:
                raise Exception("Controller", "register_models", "Invalid model type")

    @classmethod
    def save_all(cls) -> bool:
        from gws.prism.model import DbManager, Process, Resource, ViewModel
        with DbManager.db.atomic() as transaction:
            try:
                # first) save all viewable processes
                for k in cls.models:
                    if isinstance(cls.models[k], Process):
                        cls.models[k].save()
                
                # second) save all viewable resources
                for k in cls.models:
                    if isinstance(cls.models[k], Resource):
                        cls.models[k].save()

                # third) save all view_models
                for k in cls.models:
                    if isinstance(cls.models[k], ViewModel):
                        cls.models[k].save()
            except:
                transaction.rollback()
                return False

        return True
    
    @classmethod
    def _unregister_model_instances(cls, uuids: list):
        from gws.prism.model import Model
        for uuid in uuids:
            cls.models.pop(uuid,None)
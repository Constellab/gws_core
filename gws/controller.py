# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import importlib
import inspect
import asyncio

from gws.base import Base
from gws.logger import Logger
from gws.query import Query, Paginator

class Controller(Base):
    """
    Controller class
    """

    _model_specs = dict() 
    _settings = None
    _number_of_items_per_page = 50

    @classmethod
    def action(cls, action=None, object_type=None, object_uri=None, data=None, page=1, number_of_items_per_page=20, filters=[], return_format="") -> 'ViewModel':
        """
        Process user actions

        :param action: The action
        :type action: str
        :param object_type: The type of the view model
        :type object_type: str
        :param object_uri: The uri of the view model
        :type object_uri: str
        :param data: The data
        :type data: dict
        :return: A view model corresponding to the action
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
        if action == "list":
            Q = cls.fetch_list(object_type, page, filters=filters)

            if return_format == "json":
                return Paginator(Q, page=page).as_json()
            else:
                return Paginator(Q, page=page).as_model_list()

        else:
            if action == "post":
                model = cls.__post(object_type, object_uri, data)
            elif action == "get":
                model = cls.__get(object_type, object_uri)
            elif action == "put":
                model = cls.__put(object_type, object_uri, data)
            elif action == "delete":
                model = cls.__delete(object_type, object_uri)
            elif action == "run":
                model = asyncio.run( cls.__run(experiment_uri = object_uri) )
            
            if return_format == "json":
                return model.as_json()
            else:
                return model

    # -- C --

    # -- D --

    @classmethod
    def __delete(cls, object_type: str, object_uri: str) -> 'ViewModel':
        from gws.model import Model, ViewModel
        o = cls.fetch_model(object_type, object_uri)
        if isinstance(o, ViewModel):
            o.remove()
            return o
        else:
            Logger.error(Exception("Controller", f"__delete", "No ViewModel match with uri {object_uri}."))

    # -- F --

    @classmethod
    def fetch_experiment_list(cls, page=1, number_of_items_per_page=20, filters=[], return_format=""):
        from gws.model import Experiment
        Q = Experiment.select().order_by(Experiment.creation_datetime.desc())

        number_of_items_per_page = max(number_of_items_per_page, cls._number_of_items_per_page)

        if return_format == "json":
            return Paginator(Q, page=page, number_of_items_per_page=number_of_items_per_page).as_json()
        else:
            return Paginator(Q, page=page, number_of_items_per_page=number_of_items_per_page).as_model_list()
    
    @classmethod
    def fetch_job_list(cls, experiment_uri=None, page=1, number_of_items_per_page=20, filters=[], return_format=""):
        from gws.model import Job, Experiment
        Q = Job.select().order_by(Job.creation_datetime.desc())

        number_of_items_per_page = max(number_of_items_per_page, cls._number_of_items_per_page)

        if not experiment_uri is None :
            Q = Q.join(Experiment).where(Experiment.uri == experiment_uri)

        if return_format == "json":
            return Paginator(Q, page=page, number_of_items_per_page=number_of_items_per_page).as_json()
        else:
            return Paginator(Q, page=page, number_of_items_per_page=number_of_items_per_page).as_model_list()

    @classmethod
    def fetch_protocol_list(cls, experiment_uri=None, job_uri=None, page=1, number_of_items_per_page=20, filters=[], return_format=""):
        from gws.model import Protocol, Job, Experiment
        
        if experiment_uri:
            Q = Protocol.select_me()\
                            .join(Experiment, on=(Experiment.protocol_uri == Protocol.uri))\
                            .where(Experiment.uri == experiment_uri)
        elif job_uri:
            Q = Protocol.select_me()\
                            .join(Job, on=(Job.process_uri == Protocol.uri))\
                            .where(Job.uri == job_uri)
        else:
            number_of_items_per_page = max(number_of_items_per_page, cls._number_of_items_per_page)
            Q = Protocol.select_me().order_by(Protocol.creation_datetime.desc())

        if return_format == "json":
            return Paginator(Q, page=page, number_of_items_per_page=number_of_items_per_page).as_json()
        else:
            return Paginator(Q, page=page, number_of_items_per_page=number_of_items_per_page).as_model_list()

    @classmethod
    def fetch_process_list(cls, job_uri=None, page=1, number_of_items_per_page=20, filters=[], return_format=""):
        from gws.model import Process, Job

        if job_uri is None:
            number_of_items_per_page = max(number_of_items_per_page, cls._number_of_items_per_page)
            Q = Process.select().order_by(Process.creation_datetime.desc())
        else:
            Q = Process.select()\
                            .join(Job, on=(Job.process_uri == Process.uri))\
                            .where(Job.uri == job_uri) \
                            .order_by(Process.creation_datetime.desc())

        if return_format == "json":
            return Paginator(Q, page=page, number_of_items_per_page=number_of_items_per_page).as_json()
        else:
            return Paginator(Q, page=page, number_of_items_per_page=number_of_items_per_page).as_model_list()

    @classmethod
    def fetch_config_list(cls, job_uri=None, page=1, number_of_items_per_page=20, filters=[], return_format=""):
        from gws.model import Config, Job

        if job_uri is None:
            number_of_items_per_page = max(number_of_items_per_page, cls._number_of_items_per_page)
            Q = Config.select().order_by(Config.creation_datetime.desc())
        else:
            Q = Config.select()\
                            .join(Job, on=(Job.config_uri == Config.uri))\
                            .where(Job.uri == job_uri) \
                            .order_by(Config.creation_datetime.desc())

        if return_format == "json":
            return Paginator(Q, page=page, number_of_items_per_page=number_of_items_per_page).as_json()
        else:
            return Paginator(Q, page=page, number_of_items_per_page=number_of_items_per_page).as_model_list()

    @classmethod
    def fetch_resource_list(cls, experiment_uri=None, job_uri=None, page=1, number_of_items_per_page=20, filters=[], return_format=""):
        from gws.model import Resource, Job, Experiment
        
        
        if not job_uri is None:
            Q = Resource.select() \
                        .join(Job) \
                        .join(Experiment) \
                        .where(Job.uri == job_uri) \
                        .order_by(Resource.creation_datetime.desc())
        elif not experiment_uri is None: 
            Q = Resource.select() \
                        .join(Job) \
                        .join(Experiment) \
                        .where(Experiment.uri == experiment_uri) \
                        .order_by(Resource.creation_datetime.desc())
        else:
            number_of_items_per_page = max(number_of_items_per_page, cls._number_of_items_per_page)
            Q = Resource.select().order_by(Resource.creation_datetime.desc())

        if return_format == "json":
            return Paginator(Q, page=page, number_of_items_per_page=number_of_items_per_page).as_json()
        else:
            return Paginator(Q, page=page, number_of_items_per_page=number_of_items_per_page).as_model_list()


    @classmethod
    def fetch_list(cls, object_type: str, page: int=1, number_of_items_per_page: int=20, filters=[], return_format="") -> 'Model':
        t = cls.get_model_type(object_type)

        number_of_items_per_page = max(number_of_items_per_page, cls._number_of_items_per_page)
        try:
            Q = t.select().order_by(t.creation_datetime.desc())
            if len(filters) > 0:
                pass

            if return_format == "json":
                return Paginator(Q, page=page, number_of_items_per_page=number_of_items_per_page).as_json()
            else:
                return Paginator(Q, page=page, number_of_items_per_page=number_of_items_per_page).as_model_list()
        except:
            return None

    @classmethod
    def fetch_model(cls, object_type: str, object_uri: str) -> 'Model':
        """
        Fetch a model using the object_uri

        :param object_uri: The uri of the target model
        :type object_uri: str
        :return: A model
        :object_type: Model
        """

        t = cls.get_model_type(object_type)
        try:
            return t.get(t.uri == object_uri)
        except:
            return None        
    # -- G --

    @classmethod
    def get_settings(cls):
        if Controller._settings is None:
            from gws.settings import Settings
            Controller._settings = Settings.retrieve()
        
        return Controller._settings
        
    @classmethod
    def __get(cls, object_type: str, object_uri: str) -> 'ViewModel':
        obj = cls.fetch_model(object_type, object_uri)
        from gws.model import Model, ViewModel
        if isinstance(obj, ViewModel):
            return obj
        elif isinstance(obj, Model):
            return obj
        else:
            Logger.error(Exception("Controller", "__get", f"No ViewModel or Model found for the encoded uri {object_uri}"))
        

    @classmethod
    def get_model_type(cls, type_str: str) -> type:
        """
        Get the type of a registered model using its litteral type
        
        :param type_str: Litteral type (can be a slugyfied string)
        :type type_str: str
        :return: The type if the model is registered, None otherwise
        :object_type: type
        :Logger.error(Exception: No registered model matchs with the given `type_str`)
        """
   
        if type_str is None:
            return None
        
        from gws.model import Experiment, Protocol, Process, Resource, Config, Job
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
        elif type_str.lower() == "job":
            return Job

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
    def __post(cls, object_type: str, object_uri: str, data: dict) -> 'ViewModel':
        from gws.model import SystemTrackable, ViewModel
        obj = cls.fetch_model(object_type, object_uri)

        if isinstance(obj, SystemTrackable):
            Logger.error(Exception("Controller", "__post", f"Object {type(obj)} is SystemTrackable. It can only be created by the  core system"))

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
    def __post_new_model_and_return_vmodel(cls, object_type: str, object_uri: str, data: dict):
        model_t = cls.get_model_type(object_type)
        model = model_t()

        from gws.model import Model
        if not isinstance(model, Model):
            Logger.error(Exception("Controller", "action", f"Object uri {object_uri} must refer to a Model"))

        mdata = data.get("mdata", {})
        model.hydrate_with(mdata)

        vmodel = model.create_default_vmodel()
        vdata = data.get("vdata", {})
        vmodel.hydrate_with(vdata)
        vmodel.save()

        return vmodel

    @classmethod
    def __put(cls, object_type: str, object_uri: str, data: dict) -> 'ViewModel':
        from gws.model import SystemTrackable, ViewModel
        t = cls.get_model_type(object_type)
        
        try:
            obj = t.get(t.uri == object_uri)
        except:
            Logger.error(Exception("Controller", "__post", f"Object {type(obj)} is not found with uri {object_uri}"))

        if isinstance(obj, SystemTrackable):
            Logger.error(Exception("Controller", "__post", f"Object {type(obj)} is SystemTrackable. It can only be updated by the  core system"))

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

    # @classmethod
    # def register_models(cls):
    #     settings = cls.get_settings()
    #     bricks = settings.get_dependency_names()

    #     print("xxxxx")
    #     print(bricks)

    #     from gws.model import Process 
    #     for brick_name in bricks:
    #         print(brick_name)
    #         module = importlib.import_module(brick_name)
    #         for module_name, _ in inspect.getmembers(module, inspect.ismodule):
    #             submodule = importlib.import_module(brick_name+"."+module_name)
    #             for class_name, _ in inspect.getmembers(submodule, inspect.isclass):
    #                 t = getattr(submodule, class_name, None)
    #                 print(t)
    #                 if issubclass(t, Process):
    #                     print("yyyy")
    #                     print(t)
    #                     pass

    @classmethod
    async def _run_robot_travel(cls):
        from gws.robot import create_protocol
        p = create_protocol()
        e = p.create_experiment()
        e.set_title("The journey of Astro.")
        e.set_data_value("description", "This is the journey of Astro.")
        await e.run()
        e.save()
        return True
    
    @classmethod
    async def _run_robot_super_travel(cls):
        from gws.robot import create_nested_protocol
        p = create_nested_protocol()
        e = p.create_experiment()
        e.set_title("The super journey of Astro.")
        e.set_data_value("description", "This is the super journey of Astro.")
        await e.run()
        e.save()
        return True
        
    # @classmethod
    # async def __run(cls, process_type: str, process_uri: str, config_params: dict):
    #     from gws.model import Process
    #     if not process_uri is None:
    #         try:
    #             proc = Process.get(Process.uri == process_uri)
    #         except:
    #             proc = None
    #     elif not process_type is None:
    #         t = cls.get_model_type(process_type)
    #         proc = t()

    #     if isinstance(proc, Process):
    #         job = proc.get_active_job()
    #         job.config.set_params(config_params)
    #         e = proc.create_experiment()
    #         e.run()
    #         e.save()
    #     else:
    #         Logger.error(Exception("Controller", "__run", "Process not found"))

    @classmethod
    async def __run(cls, experiment_uri: str = None):
        from gws.model import Experiment
        try:
            e = Experiment.get(Experiment.uri == experiment_uri)
            await e.run()
        except Exception as err:
            Logger.error(Exception("Controller", "__run", f"An error occured. {err}"))
        
    @classmethod
    def save_all(cls, model_list: list = None) -> bool:
        """
        Atomically and safely save a list of models in the database. If an error occurs
        during the operation, the whole transactions is rolled back.
        
        :param model_list: List of models
        :type model_list: list
        :return: True if all the model are successfully saved, False otherwise. 
        :object_type: bool
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

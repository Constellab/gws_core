# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import importlib

from gws.base import Base
from gws.logger import Logger
from gws.query import Query, Paginator

class Controller(Base):
    """
    Controller class
    """

    _model_specs = dict() 
    _settings = None

    @classmethod
    def action(cls, action=None, model_type=None, uri=None, data=None, page=1, filters=[], return_format=None) -> 'ViewModel':
        """
        Process user actions

        :param action: The action
        :type action: str
        :param uri: The uri of the view model
        :type uri: str
        :param data: The data
        :type data: dict
        :return: A view model corresponding to the action
        :model_type: `gws.prims.model.ViewModel`
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
            Q = cls.fetch_list(model_type, page, filters=filters)

            if return_format == "json":
                return Paginator(Q, page=page).as_json()
            else:
                return Paginator(Q, page=page).as_model_list()

        else:
            if action == "post":
                model = cls.__post(model_type, uri, data)
            elif action == "get":
                model = cls.__get(model_type, uri)
            elif action == "put":
                model = cls.__put(model_type, uri, data)
            elif action == "delete":
                model = cls.__delete(model_type, uri)
            elif action == "run":
                model = cls.__run(data)
            
            if return_format == "json":
                return model.as_json()
            else:
                return model

    # -- C --

    # -- D --

    @classmethod
    def __delete(cls, model_type: str, uri: str) -> 'ViewModel':
        from gws.model import Model, ViewModel
        o = cls.fetch_model(model_type, uri)
        if isinstance(o, ViewModel):
            o.delete()
            return o
        else:
            Logger.error(Exception("Controller", f"__delete", "No ViewModel match with the uri."))

    # -- F --

    @classmethod
    def fetch_experiment_list(cls, page=1, filters=[], return_format=""):
        from gws.model import Experiment
        Q = Experiment.select().order_by(Experiment.creation_datetime.desc())

        if return_format == "json":
            return Paginator(Q, page=page).as_json()
        else:
            return Paginator(Q, page=page).as_model_list()
    
    @classmethod
    def fetch_job_list(cls, experiment_uri=None, page=1, filters=[], return_format=""):
        from gws.model import Job, Experiment, Process, DbManager
        Q = Job.select().order_by(Job.creation_datetime.desc())
                    
        if not experiment_uri is None :
            Q = Q.join(Experiment).where(Experiment.uri == experiment_uri)

        if return_format == "json":
            return Paginator(Q, page=page).as_json()
        else:
            return Paginator(Q, page=page).as_model_list()

    @classmethod
    def fetch_protocol_list(cls, job_uri=None, page=1, filters=[], return_format=""):
        from gws.model import Protocol, Job

        if job_uri is None:
            Q = Protocol.select_me().order_by(Protocol.creation_datetime.desc())
        else:
            try:
                job = Job.get(Job.uri == job_uri)
                Q = [ job.process ]
            except:
                return None

        if return_format == "json":
            return Paginator(Q, page=page).as_json()
        else:
            return Paginator(Q, page=page).as_model_list()

    @classmethod
    def fetch_process_list(cls, job_uri=None, page=1, filters=[], return_format=""):
        from gws.model import Process, Job

        if job_uri is None:
            Q = Process.select().order_by(Process.creation_datetime.desc())
        else:
            Q = Process.select()\
                            .join(Job, on=(Job.process_id == Process.id))\
                            .where(Job.uri == job_uri) \
                            .order_by(Process.creation_datetime.desc())

        if return_format == "json":
            return Paginator(Q, page=page).as_json()
        else:
            return Paginator(Q, page=page).as_model_list()

    @classmethod
    def fetch_config_list(cls, job_uri=None, page=1, filters=[], return_format=""):
        from gws.model import Config, Job

        if job_uri is None:
            Q = Config.select().order_by(Config.creation_datetime.desc())
        else:
            Q = Config.select()\
                            .join(Job, on=(Job.config_id == Config.id))\
                            .where(Job.uri == job_uri) \
                            .order_by(Config.creation_datetime.desc())

        if return_format == "json":
            return Paginator(Q, page=page).as_json()
        else:
            return Paginator(Q, page=page).as_model_list()

    @classmethod
    def fetch_resource_list(cls, experiment_uri=None, job_uri=None, page=1, filters=[], return_format=""):
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
            Q = Resource.select().order_by(Resource.creation_datetime.desc())

        if return_format == "json":
            return Paginator(Q, page=page).as_json()
        else:
            return Paginator(Q, page=page).as_model_list()


    @classmethod
    def fetch_list(cls, model_type: str, page: int, filters=[], return_format="") -> 'Model':
        t = cls.get_model_type(model_type)
        try:
            Q = t.select().order_by(t.creation_datetime.desc())
            if len(filters) > 0:
                pass

            if return_format == "json":
                return Paginator(Q, page=page).as_json()
            else:
                return Paginator(Q, page=page).as_model_list()
        except:
            return None

    @classmethod
    def fetch_model(cls, model_type: str, uri: str) -> 'Model':
        """
        Fetch a model using the uri

        :param uri: The uri of the target model
        :type uri: str
        :return: A model
        :model_type: Model
        """

        t = cls.get_model_type(model_type)
        try:
            return t.get(t.uri == uri)
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
    def __get(cls, model_type: str, uri: str) -> 'ViewModel':
        obj = cls.fetch_model(model_type, uri)
        from gws.model import Model, ViewModel
        if isinstance(obj, ViewModel):
            return obj
        elif isinstance(obj, Model):
            return obj
        else:
            Logger.error(Exception("Controller", "__get", f"No ViewModel or Model found for the encoded uri {uri}"))
        

    @classmethod
    def get_model_type(cls, type_str: str) -> type:
        """
        Get the type of a registered model using its litteral type
        
        :param type_str: Litteral type (can be a slugyfied string)
        :type type_str: str
        :return: The type if the model is registered, None otherwise
        :model_type: type
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
    def __post(cls, model_type: str, uri: str, data: dict) -> 'ViewModel':
        from gws.model import SystemTrackable, ViewModel
        obj = cls.fetch_model(model_type, uri)

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
    def __post_new_model_and_return_vmodel(cls, model_type: str, uri: str, data: dict):
        model_t = cls.get_model_type(model_type)
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
    def __put(cls, model_type: str, uri: str, data: dict) -> 'ViewModel':
        from gws.model import SystemTrackable, ViewModel
        t = cls.get_model_type(model_type)
        
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
    async def _run_robot(cls):
        from gws.robot import create_protocol
        from gws.model import Experiment
        e = Experiment()
        e.set_title("A unexpected journey of Astro Boy")
        e.set_data_value("description", "This is a unexpected journey of Astro.")
        p = create_protocol()
        p.set_active_experiment(e)
        e.save()
        await p.run()
        return p.save()
        
    @classmethod
    async def __run(cls, process_type: str, process_uri: str, config_params: dict):
        from gws.model import Process
        if not process_uri is None:
            try:
                proc = Process.get(Process.uri == process_uri)
            except:
                proc = None
        elif not process_type is None:
            t = cls.get_model_type(process_type)
            proc = t()

        if isinstance(proc, Process):
            job = proc.get_active_job()
            job.config.set_params(config_params)
            await proc.run()
        else:
            Logger.error(Exception("Controller", "__run", "Process not found"))

    @classmethod
    def save_all(cls, model_list: list = None) -> bool:
        """
        Atomically and safely save a list of models in the database. If an error occurs
        during the operation, the whole transactions is rolled back.
        
        :param model_list: List of models
        :type model_list: list
        :return: True if all the model are successfully saved, False otherwise. 
        :model_type: bool
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

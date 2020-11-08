# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import importlib

from gws.base import Base
from gws.logger import Logger

NUMBER_OF_ITEMS_PER_PAGE = 20

class Controller(Base):
    """
    Controller class
    """

    _model_specs = dict() 

    @classmethod
    def action(cls, action=None, rtype=None, uri=None, data=None, return_format="", page=1, filters=[]) -> 'ViewModel':
        """
        Process user actions

        :param action: The action
        :type action: str
        :param uri: The uri of the view model
        :type uri: str
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
        if action == "list":
            Q = cls.fetch_list(rtype, page, filters=filters)
            return cls.__get_query_as_list(Q, return_format=return_format)
        else:
            if action == "post":
                model = cls.__post(rtype, uri, data)
            elif action == "get":
                model = cls.__get(rtype, uri)
            elif action == "put":
                model = cls.__put(rtype, uri, data)
            elif action == "delete":
                model = cls.__delete(rtype, uri)
            elif action == "run":
                model = cls.__run(data)
            
            if return_format.lower() == "json":
                return model.as_json()
            else:
                return model

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
    def fetch_experiment_list(cls, return_format="", page=1, filters=[]):
        from gws.model import Experiment
        Q = Experiment.select().paginate(page, NUMBER_OF_ITEMS_PER_PAGE)
        return cls.__get_query_as_list(Q, return_format=return_format)
    
    @classmethod
    def fetch_job_list(cls, experiment_uri=None, return_format="", page=1, filters=[]):
        from gws.model import Job, Experiment, Process, DbManager
        Q = Job.select() \
                    .paginate(page, NUMBER_OF_ITEMS_PER_PAGE)

        if not experiment_uri is None :
            Q = Q.join(Experiment).where(Experiment.uri == experiment_uri)

        # if not process_uri is None :
        #     # cursor = DbManager.db.execute_sql('SELECT id FROM process WHERE uri = ?', (process_uri,))
        #     # row = cursor.fetchone()
        #     # if len(row) == 0:
        #     #     return None

        #     # _id = row[0]
        #     # Q = Q.where(Job.process_id == _id)
            
        return cls.__get_query_as_list(Q, return_format=return_format)

    @classmethod
    def fetch_protocol_list(cls, job_uri=None, return_format="", page=1, filters=[]):
        from gws.model import Protocol, Job

        if job_uri is None:
            Q = Protocol.select_me().paginate(page, NUMBER_OF_ITEMS_PER_PAGE)
        else:
            try:
                job = Job.get(Job.uri == job_uri)
                Q = [ job.process ]
            except:
                return None

        return cls.__get_query_as_list(Q, return_format=return_format)

    @classmethod
    def fetch_process_list(cls, job_uri=None, return_format="", page=1, filters=[]):
        from gws.model import Process, Job

        if job_uri is None:
            Q = Process.select().paginate(page, NUMBER_OF_ITEMS_PER_PAGE)
        else:
            try:
                job = Job.get(Job.uri == job_uri)
                Q = [ job.process ]
            except:
                return None

        return cls.__get_query_as_list(Q, return_format=return_format)

    @classmethod
    def fetch_config_list(cls, job_uri=None, return_format="", page=1, filters=[]):
        from gws.model import Config, Job

        if job_uri is None:
            Q = Config.select().paginate(page, NUMBER_OF_ITEMS_PER_PAGE)
        else:
            try:
                job = Job.get(Job.uri == job_uri)
                Q = [ job.config ]
            except:
                return None

        return cls.__get_query_as_list(Q, return_format=return_format)

    @classmethod
    def fetch_resource_list(cls, experiment_uri=None, job_uri=None, return_format="", page=1, filters=[]):
        from gws.model import Resource, Job, Experiment
        
        if not experiment_uri is None: 
            Q = Resource.select() \
                        .join(Job) \
                        .join(Experiment) \
                        .where(Experiment.uri == experiment_uri)
        elif not job_uri is None:
            try:
                job = Job.get(Job.uri == job_uri)
                Q = job.resources
            except:
                Q = []
        else:
            Q = Resource.select().paginate(page, NUMBER_OF_ITEMS_PER_PAGE)

        return cls.__get_query_as_list(Q, return_format=return_format)


    @classmethod
    def fetch_list(cls, rtype: str, page: int, filters=[]) -> 'Model':
        t = cls.get_model_type(rtype)
        try:
            Q = t.select().paginate(page, NUMBER_OF_ITEMS_PER_PAGE)
            if len(filters) > 0:
                pass
            return Q
        except:
            return None

    @classmethod
    def fetch_model(cls, rtype: str, uri: str) -> 'Model':
        """
        Fetch a model using the uri

        :param uri: The uri of the target model
        :type uri: str
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
    def __get_query_as_list(cls, Q, return_format=""):
        _list = []
        if return_format.lower() == "json":
            for o in Q:
                _list.append(o.as_json())
        else:
            for o in Q:
                _list.append(o)
        
        return _list

    @classmethod
    def __get(cls, rtype: str, uri: str) -> 'ViewModel':
        obj = cls.fetch_model(rtype, uri)
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
        :rtype: type
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
    async def _run_robot(cls):
        from gws.robot import create_protocol
        from gws.model import Experiment
        e = Experiment()
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

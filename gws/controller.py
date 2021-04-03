# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import json
import importlib
import inspect
import asyncio

from gws.base import Base
from gws.logger import Error, Info
from gws.query import Query, Paginator
from gws.http import *

from typing import List
from fastapi import UploadFile, File as FastAPIFile
from starlette_context import context

class Controller(Base):
    """
    Controller class
    """

    _session = None
    _model_specs = dict() 
    _settings = None
    _number_of_items_per_page = 50

    @classmethod
    async def action(cls, action=None, object_type=None, object_uri=None, study_uri=None, data=None, page=1, number_of_items_per_page=20, filters="") -> 'ViewModel':
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
            raise Error("Controller", "action", "The data is not a valid JSON text")
        
        if action == "get":
            object_uris = object_uri.split(",")
            if len(object_uris) == 1 and not "all" in object_uris:
                model = cls.__action_get(object_type, object_uri, data)
            else:
                model = cls.__action_list(
                    object_type, object_uris, data=data, 
                    page=page, number_of_items_per_page=number_of_items_per_page
                )
        elif action == "update":
            # update objects
            model = cls.__action_update(object_type, object_uri, data)
        elif action == "delete":
            model = cls.__action_delete(object_type, object_uri)
        elif action == "upload":
            model = await cls.__action_upload(data, study_uri=study_uri)
        elif action == "count":
            model = cls.__action_count(object_type)
            
        return model
    
    @classmethod
    def __action_count(cls, object_type: str) -> int:
        t = cls.get_model_type(object_type)
        if t is None:
            raise HTTPNotFound(detail=f"Invalid Model type")

        return t.select().count()
    
    @classmethod
    def __action_get(cls, object_type: str, object_uri: str, data:dict=None) -> 'ViewModel':
        obj = cls.fetch_model(object_type, object_uri)
        if obj is None:
            raise HTTPNotFound(detail=f"Invalid Model type or uri not found")
        
        from gws.model import Model, ViewModel
        if isinstance(obj, ViewModel):
            # Ok!
            pass
        elif isinstance(obj, Model):
            obj = obj.view(params=data)
        else:
            raise HTTPNotFound(detail=f"No Model found with uri {object_uri}")
        
        return obj.as_json()

    @classmethod
    def __action_delete(cls, object_type: str, object_uri: str) -> 'ViewModel':
        from gws.model import Model, ViewModel
        obj = cls.fetch_model(object_type, object_uri)
        
        if obj is None:
            raise HTTPNotFound(detail=f"Invalid Model type or uri not found")

        if isinstance(obj, ViewModel):
            obj.remove()
            return obj.as_json()
        else:
            raise HTTPNotFound(detail=f"No ViewModel found with uri {object_uri}")
    
    @classmethod
    def __action_list(cls, object_type: str, object_uris: list,  data:dict=None, page=1, number_of_items_per_page=20) -> list:
        t = cls.get_model_type(object_type)
        
        if t is None:
            raise HTTPNotFound(detail=f"Invalid Model type")
        
        number_of_items_per_page = min(number_of_items_per_page, cls._number_of_items_per_page)
        
        if "all" in object_uris:
            q = data.get("filter","")
            if q:
                Q = t.search(**q)

                p = Paginator(Q, page=page, number_of_items_per_page=number_of_items_per_page, view_params=data)
                result = []
                for o in p:
                    if return_format=="json":
                        result.append( o.get_related().as_json() )
                    else:
                        result.append(o)

                return {
                    'data' : result,
                    'paginator': p._paginator_dict()
                }
            else:
                Q = t.select() #.order_by(t.creation_datetime.desc())
                return Paginator(Q, page=page, number_of_items_per_page=number_of_items_per_page, view_params=data).as_json()
        else:
            Q = t.select(t.uri.in_(object_uris)) #.order_by(t.creation_datetime.desc())
            return Paginator(Q, page=page, number_of_items_per_page=number_of_items_per_page, view_params=data).as_json()

    @classmethod
    def __action_update(cls, object_type: str, object_uri: str, data: dict) -> 'ViewModel':
        from gws.model import ViewModel        
        obj = cls.fetch_model(object_type, object_uri)
        if obj is None:
            raise HTTPNotFound(detail=f"Invalid Model type or uri not found")
        
        if isinstance(obj, ViewModel):
            view_model = obj
            view_model.set_params(data)
            view_model.save()
        else:
            raise HTTPNotFound(detail=f"No ViewModel found with uri {object_uri}")

        return view_model.as_json()

    @classmethod
    async def __action_upload(cls, files: List[UploadFile] = FastAPIFile(...), study_uri=None):
        from gws.model import Study
        from gws.file import Uploader
        u = Uploader(files=files)

        if study_uri is None:
            e = u.create_experiment(study = Study.get_default_instance())
        else:
            try:
                study = Study.get(Study.uri == study_uri)
                e = u.create_experiment(study = study)
            except:
                raise HTTPNotFound(detail=f"Study not found")

        try:
            await e.run()
            result = u.output["result"]
            return result.as_json()
        except Exception as err:
            raise HTTPInternalServerError(detail=f"Upload failed. Error: {err}")

    # -- C --
    
    
    # -- F --

        
    @classmethod
    def fetch_experiment_list(cls, page=1, number_of_items_per_page=20, filters=[]):
        from gws.model import Experiment
        Q = Experiment.select().order_by(Experiment.creation_datetime.desc())
        number_of_items_per_page = min(number_of_items_per_page, cls._number_of_items_per_page)
        return Paginator(Q, page=page, number_of_items_per_page=number_of_items_per_page).as_json()
    
    @classmethod
    def fetch_job_list(cls, experiment_uri=None, page=1, number_of_items_per_page=20, filters=[]):
        from gws.model import Job, Experiment
        Q = Job.select().order_by(Job.creation_datetime.desc())
        number_of_items_per_page = min(number_of_items_per_page, cls._number_of_items_per_page)
        if not experiment_uri is None :
            Q = Q.join(Experiment).where(Experiment.uri == experiment_uri)

        return Paginator(Q, page=page, number_of_items_per_page=number_of_items_per_page).as_json()
    
    @classmethod
    def fetch_job_flow(cls, protocol_job_uri=None, experiment_uri=None):
        from gws.model import Experiment, Job
        
        try:
            if protocol_job_uri:
                job = Job.get(Job.uri == protocol_job_uri)
            elif experiment_uri:
                e = Experiment.get(Experiment.uri == experiment_uri)
                job = e.job
            
            return job.flow
        except Exception as err:
            raise HTTPInternalServerError(detail=f"An error occured. Error: {err}")
            
    
    @classmethod
    def fetch_protocol_list(cls, experiment_uri=None, job_uri=None, page=1, number_of_items_per_page=20):
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
            number_of_items_per_page = min(number_of_items_per_page, cls._number_of_items_per_page)
            Q = Protocol.select_me().order_by(Protocol.creation_datetime.desc())

        return Paginator(Q, page=page, number_of_items_per_page=number_of_items_per_page).as_json()
    
    @classmethod
    def fetch_process_list(cls, job_uri=None, page=1, number_of_items_per_page=20):
        from gws.model import Process, Job

        if job_uri is None:
            number_of_items_per_page = min(number_of_items_per_page, cls._number_of_items_per_page)
            Q = Process.select().order_by(Process.creation_datetime.desc())
        else:
            Q = Process.select()\
                            .join(Job, on=(Job.process_uri == Process.uri))\
                            .where(Job.uri == job_uri) \
                            .order_by(Process.creation_datetime.desc())

        return Paginator(Q, page=page, number_of_items_per_page=number_of_items_per_page).as_json()

    @classmethod
    def fetch_config_list(cls, job_uri=None, page=1, number_of_items_per_page=20):
        from gws.model import Config, Job

        if job_uri is None:
            number_of_items_per_page = min(number_of_items_per_page, cls._number_of_items_per_page)
            Q = Config.select().order_by(Config.creation_datetime.desc())
        else:
            Q = Config.select()\
                            .join(Job, on=(Job.config_uri == Config.uri))\
                            .where(Job.uri == job_uri) \
                            .order_by(Config.creation_datetime.desc())

        return Paginator(Q, page=page, number_of_items_per_page=number_of_items_per_page).as_json()

    @classmethod
    def fetch_resource_list(cls, experiment_uri=None, job_uri=None, page=1, number_of_items_per_page=20):
        from gws.model import Resource, Job, Experiment
        
        if job_uri:
            Q = Resource.select() \
                        .join(Job) \
                        .join(Experiment) \
                        .where(Job.uri == job_uri) \
                        .order_by(Resource.creation_datetime.desc())
        elif experiment_uri: 
            Q = Resource.select() \
                        .join(Job) \
                        .join(Experiment) \
                        .where(Experiment.uri == experiment_uri) \
                        .order_by(Resource.creation_datetime.desc())
        else:
            number_of_items_per_page = min(number_of_items_per_page, cls._number_of_items_per_page)
            Q = Resource.select().order_by(Resource.creation_datetime.desc())

        return Paginator(Q, page=page, number_of_items_per_page=number_of_items_per_page).as_json()
    
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
        
        if t is None:
            return None
        
        try:
            return t.get(t.uri == object_uri)
        except:
            return None        
    
    # -- G --
    
    @classmethod
    def get_current_user(cls):
        try:
            return context.data["user"]
        except:
            return None
            
    
    @classmethod
    def get_settings(cls):
        if Controller._settings is None:
            from gws.settings import Settings
            Controller._settings = Settings.retrieve()
        
        return Controller._settings
               
    @classmethod
    def get_model_type(cls, type_str: str) -> type:
        """
        Get the type of a registered model using its litteral type
        
        :param type_str: Litteral type (can be a slugyfied string)
        :type type_str: str
        :return: The type if the model is registered, None otherwise
        :object_type: type
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
        
        try:
            module = importlib.import_module(module_name)
            t = getattr(module, function_name, None)
        except:
            t = None
 
        return t

    # -- L --

    # -- P --

    # -- R --
    
    @classmethod
    def __list_sub_module(cls, cdir):
        import glob
        modules = glob.glob(os.path.join(cdir, "*.py"))
        return [ os.path.basename(f)[:-3] for f in modules if os.path.isfile(f) and not f.endswith('__init__.py')]
    
    
    @classmethod
    def register_all_processes(cls):
        settings = cls.get_settings()
        dep_dirs = settings.get_dependency_dirs()

        from gws.model import Process, Protocol
        process_type_list = []
        
        for brick_name in dep_dirs:
            cdir = dep_dirs[brick_name]
            module_names = cls.__list_sub_module( os.path.join(cdir, brick_name) )
  
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
                        is_process_and_not_protocol = issubclass(t, Process) and not issubclass(t, Protocol)
                        if is_process_and_not_protocol:
                            process_type_list.append(t)
                except:
                    pass
        
        process_type_list = list(set(process_type_list))
        for proc_t in set(process_type_list):
            try:
                proc_t.get(proc_t.type == proc_t.full_classname())
            except:
                if not t == Protocol:
                    proc = proc_t()
                    proc.save()
        
        Info(f"REGISTER_ALL_PROCESSES: A total of {len(process_type_list)} processes were registered in db.\n Process list:\n {process_type_list}")

    @classmethod
    async def _run_robot_travel(cls):
        from gws.model import Study
        from gws.robot import create_protocol
        p = create_protocol()
        e = p.create_experiment(study = Study.get_default_instance())
        e.set_title("The journey of Astro.")
        e.data["description"] = "This is the journey of Astro."
        
        try:
            await e.run()
            return e.view().as_json()
        except Exception as err:
            raise HTTPInternalServerError(detail=f"An error occured. Error: {err}")
            
    @classmethod
    async def _run_robot_super_travel(cls):
        from gws.model import Study
        from gws.robot import create_nested_protocol
        p = create_nested_protocol()
        e = p.create_experiment(study = Study.get_default_instance())
        e.set_title("The super journey of Astro.")
        e.data["description"] = "This is the super journey of Astro."
        
        try:
            await e.run()
            return e.view().as_json()
        except Exception as err:
            raise HTTPInternalServerError(detail=f"An error occured. Error: {err}")
                
    @classmethod
    async def run_experiment(cls, user, data: dict=None):
        from gws.model import Experiment
        
        try:
            e = Experiment.from_flow(data, user=Controller.get_current_user())
        except Exception as err:
            raise HTTPInternalServerError(detail=f"An error occured. Error: {err}")
        
        if not e:
            raise HTTPNotFound(detail=f"Experiment not found")
            
        if e.is_runnnig:
            raise HTTPBusy(detail=f"The experiment is already running")
        elif e.is_finished:
            raise HTTPForbiden(detail=f"The experiment is finished")
        else:
            try:
                await e.run(user=Controller.get_current_user())
                return e.view().as_json()
            except Exception as err:
                raise HTTPInternalServerError(detail=f"An error occured. Error: {err}")
    
    # -- U --
          
    # -- S --
    
    @classmethod
    def save_protocol(cls, data: dict=None):
        from gws.model import Experiment
        
        try:
            proto = Protocol.from_flow(data, user=Controller.get_current_user())
            return proto.view().as_json()
        except Exception as err:
            raise HTTPInternalServerError(detail=f"An error occured. Error: {err}")
    
    @classmethod
    def save_experiment(cls, data=None):
        from gws.model import Experiment
        
        try:
            e = Experiment.from_flow(data, user=Controller.get_current_user())
        except Exception as err:
            raise HTTPInternalServerError(detail=f"An error occured. Error: {err}")
                
        if not e:
            raise HTTPNotFound(detail=f"Cannot save the experiment")
       
        return e.view().as_json()
            
    @classmethod
    def save_all(cls, process_type_list: list = None) -> bool:
        """
        Atomically and safely save a list of models in the database. If an error occurs
        during the operation, the whole transactions is rolled back.
        
        :param process_type_list: List of models
        :type process_type_list: list
        :return: True if all the model are successfully saved, False otherwise. 
        :object_type: bool
        """
        from gws.base import DbManager
        from gws.model import Process, Resource, ViewModel
        with DbManager.db.atomic() as transaction:
            try:
                if process_type_list is None:
                    return
                    #process_type_list = cls.models.values()
                
                # 1) save processes
                for m in process_type_list:
                    if isinstance(m, Process):
                        m.save()
                
                # 2) save resources
                for m in process_type_list:
                    if isinstance(m, Resource):
                        m.save()

                # 3) save vmodels
                for m in process_type_list:
                    if isinstance(m, ViewModel):
                        m.save()
            except:
                transaction.rollback()
                return False

        return True
    
    @classmethod
    def set_current_user(cls, user: ('User', 'UserData', )):
        from gws.model import User
        from gws._api._auth_user import UserData

        if isinstance(user, UserData):
            try:
                user = User.get(User.uri==user.uri)
            except:
                raise HTTPInternalServerError(detail=f"Invalid current user")
        
        if not isinstance(user, User):
            raise HTTPInternalServerError(detail=f"Invalid current user")

        if not user.is_active:
            raise HTTPUnauthorized(detail=f"Not authorized")
            
        context.data["user"] = user
    
    # -- V --
    
    def validate_experiment(self, uri, user):
        from gws.model import Experiment
        
        try:
            e = Experiment.get(Experiment.uri == uri)
            e.validate(user=self.get_current_user())
        except Exception as err:
            raise HTTPNotFound(detail=f"Experiment not found")
        
    def validate_protocol(self, uri, user):
        from gws.model import Protocol
        
        try:
            p = Protocol.get(Protocol.uri == uri)
            p.validate(user=self.get_current_user())
        except Exception as err:
            raise HTTPNotFound(detail=f"Protocol not found")
    
# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws.query import Paginator
from gws.model import Study, Experiment
from gws.queue import Queue, Job
from gws.http import *

from .user_service import UserService
from .base_service import BaseService

class ExperimentService(BaseService):
    
    # -- C --
    
    @classmethod
    def create_experiment(cls, study_uri:str, uri: str=None, title:str=None, decription:str=None, data: dict=None):
        try:
            study = Study.get(Study.uri==study_uri)
            
            if data:
                proto = Protocol.from_graph(data)
            else:
                proto = Protocol()
                
            e = proto.create_experiment(
                uri = uri,
                user = UserService.get_current_user(), 
                study = study
            )
            
            if title:
                e.set_title(title)
                
            if description:
                e.set_description(decription)
            
            e.save()
            return e.to_json()
        except Exception as err:
            raise HTTPInternalServerError(detail=f"An error occured. Error: {err}")
   

    # -- F --
    
    @classmethod
    def fetch_experiment(cls, uri=None):
        try:
            e = Experiment.get(Experiment.uri == uri)
        except Exception as err:
            raise HTTPNotFound(detail=f"No experiment found with uri {uri}")
            
        return e.to_json()
    
    @classmethod
    def fetch_experiment_list(cls, page=1, number_of_items_per_page=20, filters=[]):
        Q = Experiment.select()\
                        .order_by(Experiment.creation_datetime.desc())
        number_of_items_per_page = min(number_of_items_per_page, cls._number_of_items_per_page)
        return Paginator(Q, page=page, number_of_items_per_page=number_of_items_per_page).to_json(shallow=True)
  
    # -- G --
    
    @classmethod
    def get_queue(cls):
        from gws.queue import Queue
        q = Queue()
        return q.to_json()
    
    # -- S --
    
    @classmethod
    async def start_experiment(cls, uri):
        try:
            e = Experiment.get(Experiment.uri == uri)
        except Exception as err:
            raise HTTPInternalServerError(detail=f"An error occured. Error: {err}")
  
        if e._is_running:
            raise HTTPForbiden(detail=f"The experiment is already running")
        elif e._is_finished:
            raise HTTPForbiden(detail=f"The experiment is finished")
        else:
            try:
                q = Queue()
                user = UserService.get_current_user()
                job = Job(user=user, experiment=e)
                q.add(job, auto_start=True)
                return e.to_json()
            except Exception as err:
                raise HTTPInternalServerError(detail=f"An error occured. Error: {err}")
    
    @classmethod
    async def stop_experiment(cls, uri):
        try:
            e = Experiment.get(Experiment.uri == uri)
        except Exception as err:
            raise HTTPInternalServerError(detail=f"An error occured. Error: {err}")
        
        if not e:
            raise HTTPNotFound(detail=f"Experiment not found")
            
        if not e._is_running:
            raise HTTPForbiden(detail=f"The experiment is not running")
        elif e._is_finished:
            raise HTTPForbiden(detail=f"The experiment is already finished")
        else:
            try:
                await e.kill_pid()
                return e.to_json()
            except Exception as err:
                raise HTTPInternalServerError(detail=f"An error occured. Error: {err}")
                
    # -- U --
     
    @classmethod
    def update_experiment(cls, uri, title=None, description=None, data: dict=None):        
        try:
            e = Experiment.get(Experiment.uri == uri)
            if not e.is_draft:
                raise HTTPInternalServerError(detail=f"The experiment is not a draft")
            
            if data:
                proto = e.protocol
                proto._build_from_dump(data, rebuild=True)
                proto.save()
            
            if title:
                e.set_title(title)
                
            if description:
                e.set_description(description)
                
            e.save()
            return e.to_json()
        except Exception as err:
            raise HTTPInternalServerError(detail=f"An error occured. Error: {err}")
            
    # -- V --
    
    @classmethod
    def validate_experiment(cls, uri):
        try:
            e = Experiment.get(Experiment.uri == uri)
        except:
            raise HTTPNotFound(detail=f"Experiment found")
        
        try:
            e.validate(user = UserService.get_current_user())
            return e.to_json()
        except Exception as err:
            raise HTTPNotFound(detail=f"Cannot validate experiment. Error: {err}")
            
            
# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from ..dto.experiment_dto import ExperimentDTO
from ..query import Paginator
from ..study import Study
from ..experiment import Experiment
from ..protocol import Protocol
from ..queue import Queue, Job
from ..http import *
from .user_service import UserService
from .base_service import BaseService

class ExperimentService(BaseService):
    
    # -- C --

    @classmethod
    def create_experiment(cls, experiment: ExperimentDTO) -> Experiment:
        try:
            study = Study.get_default_instance()
            proto = Protocol()
            e = proto.create_experiment(
                user=UserService.get_current_user(), 
                study=study
            )
            
            if experiment.title:
                e.set_title(experiment.title)
                
            if experiment.description:
                e.set_description(experiment.description)
            
            e.save()
            return e
        except Exception as err:
            raise HTTPInternalServerError(detail=f"An error occured.", debug_error=err) from err

    # -- F --
    
    @classmethod
    def fetch_experiment(cls, uri=None)-> (Experiment, dict, ):
        try:
            e = Experiment.get(Experiment.uri == uri)
        except Exception as err:
            raise HTTPNotFound(detail=f"No experiment found with uri {uri}", debug_error=err) from err
            
        return e
    
    @classmethod
    def fetch_experiment_list(cls, \
                              search_text: str="", \
                              page: int=1, \
                              number_of_items_per_page: int=20, \
                              as_json: bool = False) -> (Paginator, List[Experiment], List[dict], ):
        
        number_of_items_per_page = min(number_of_items_per_page, cls._number_of_items_per_page)
        
        if search_text:
            query = Experiment.search(search_text)
            result = []
            for o in query:
                if as_json:
                    result.append(o.get_related().to_json(shallow=True))
                else:
                    result.append(o.get_related())
            
            paginator = Paginator(query, page=page, number_of_items_per_page=number_of_items_per_page)
            return {
                'data' : result,
                'paginator': paginator._paginator_dict()
            }
        else:
            query = Experiment.select().order_by(Experiment.creation_datetime.desc())
            paginator = Paginator(query, page=page, number_of_items_per_page=number_of_items_per_page)
 
            if as_json:
                return paginator.to_json(shallow=True)
            else:
                return paginator

    # -- G --
    
    @classmethod
    def get_queue(cls) -> 'Queue':
        q = Queue()
        return q
    
    # -- S --
    
    @classmethod
    async def start_experiment(cls, uri) -> Experiment:
        try:
            e = Experiment.get(Experiment.uri == uri)
        except Exception as err:
            raise HTTPNotFound(detail=f"Experiment '{uri}' not found", debug_error=err) from err
  
        if e._is_running:
            raise HTTPForbiden(detail=f"The experiment '{uri}' is running")
        elif e._is_finished:
            if not e.reset():
                raise HTTPForbiden(detail=f"The experiment '{uri}' is finished and cannot be reset")

        try:
            q = Queue()
            user = UserService.get_current_user()
            job = Job(user=user, experiment=e)
            q.add(job, auto_start=True)
            return e
        except Exception as err:
            raise HTTPInternalServerError(detail=f"An error occured.", debug_error=err) from err
    
    @classmethod
    async def stop_experiment(cls, uri) -> Experiment:
        try:
            e = Experiment.get(Experiment.uri == uri)
        except Exception as err:
            raise HTTPInternalServerError(detail=f"Experiment '{uri}' not found") from err

        if not e._is_running:
            raise HTTPForbiden(detail=f"Experiment '{uri}' is not running")
        elif e._is_finished:
            raise HTTPForbiden(detail=f"Experiment '{uri}' is already finished")
        else:
            try:
                e.kill_pid()
                return e
            except Exception as err:
                raise HTTPInternalServerError(detail=f"Cannot kill experiment '{uri}'", debug_error=err) from err
                
    # -- U --

    @classmethod
    def update_experiment(cls, uri, experiment: ExperimentDTO) -> Experiment:
        try:
            e = Experiment.get(Experiment.uri == uri)
            if not e.is_draft:
                raise HTTPInternalServerError(detail=f"Experiment '{uri}' is not a draft")
            
            if experiment.graph:
                proto = e.protocol
                proto._build_from_dump(graph=experiment.graph, rebuild=True)
                proto.save()
            
            if experiment.title:
                e.set_title(experiment.title)
                
            if experiment.description:
                e.set_description(experiment.description)
                
            e.save()
            return e
        except Exception as err:
            raise HTTPInternalServerError(detail=f"An error occured.", debug_error=err) from err
    
            
    # -- V --
    
    @classmethod
    def validate_experiment(cls, uri) -> Experiment:
        try:
            e = Experiment.get(Experiment.uri == uri)
        except Exception as err:
            raise HTTPNotFound(detail=f"Experiment '{uri}' not found") from err
        
        try:
            e.validate(user = UserService.get_current_user())
            return e
        except Exception as err:
            raise HTTPNotFound(detail=f"Cannot validate experiment '{uri}'", debug_error=err) from err
            
            
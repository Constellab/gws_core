# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws.query import Paginator
from gws.typing import ProcessType
from gws.model import Process, Experiment
from gws.http import *

from .base_service import BaseService

class ProcessService(BaseService):
    
    # -- F --
    
    @classmethod
    def fetch_process_list(cls, experiment_uri=None, page=1, number_of_items_per_page=20, filters=[]):
        Q = Process.select()\
                    .order_by(Process.creation_datetime.desc())
        number_of_items_per_page = min(number_of_items_per_page, cls._number_of_items_per_page)
        
        if not experiment_uri is None :
            Q = Q.join(Experiment, on=(Process.experiment_id == Experiment.id))\
                    .where(Experiment.uri == experiment_uri)

        return Paginator(Q, page=page, number_of_items_per_page=number_of_items_per_page).to_json(shallow=True)      
 
    @classmethod
    def fetch_process_type_list(cls, base_ptype=None, page=1, number_of_items_per_page=20, filters=[]):
        Q = ProcessType.select()\
                        .order_by(ProcessType.ptype.desc())
        
        if base_ptype == "process":
            Q = Q.where(ProcessType.base_ptype=="gws.model.Process")
        elif base_ptype == "protocol":
            Q = Q.where(ProcessType.base_ptype=="gws.model.Protocol")
            
        number_of_items_per_page = min(number_of_items_per_page, cls._number_of_items_per_page)
        return Paginator(Q, page=page, number_of_items_per_page=number_of_items_per_page).to_json(shallow=True) 
            
            
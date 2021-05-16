# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws.model import Study
from gws.robot import create_protocol
from gws.queue import Queue, Job
from gws.http import *

from .base_service import BaseService

class AstroService(BaseService):

    @classmethod
    async def run_robot_travel(cls):
        from gws.service.user_service import UserService
        
        user = UserService.get_current_user()
        study = Study.get_default_instance()
        p = create_protocol()
        e = p.create_experiment(study=study, user=user)
        e.set_title("The journey of Astro.")
        e.data["description"] = "This is the journey of Astro."
        e.save()
        
        try:
            job = Job(user=user, experiment=e)
            Queue.add(job)
            #await e.run()
            return e.view().to_json()
        except Exception as err:
            raise HTTPInternalServerError(detail=f"An error occured. Error: {err}")
            
    @classmethod
    async def run_robot_super_travel(cls):    
        from gws.service.user_service import UserService
        
        user = UserService.get_current_user()
        study = Study.get_default_instance()
        p = create_nested_protocol()
        e = p.create_experiment(study=study, user=user)
        e.set_title("The super journey of Astro.")
        e.data["description"] = "This is the super journey of Astro."
        e.save()
        
        try:
            job = Job(user=user, experiment=e)
            Queue.add(job)
            #await e.run()
            return e.view().to_json()
        except Exception as err:
            raise HTTPInternalServerError(detail=f"An error occured. Error: {err}")
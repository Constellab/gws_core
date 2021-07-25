# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from ..study import Study
from ..robot import create_protocol, create_nested_protocol
from ..queue import Queue, Job
from ..exception.bad_request_exception import BadRequestException
from .base_service import BaseService

class AstroService(BaseService):

    @classmethod
    async def run_robot_travel(cls):
        from .user_service import UserService
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
            return e
        except Exception as err:
            raise BadRequestException(detail=f"Cannot run robot_travel") from err
            
    @classmethod
    async def run_robot_super_travel(cls):    
        from .user_service import UserService
        
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
            return e
        except Exception as err:
            raise BadRequestException(detail=f"Cannot run robot_super_travel.") from err
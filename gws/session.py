# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws.base import Base
from gws.logger import Logger


class Session(Base):
    _user = None
    _project = None
    _experiment = None 
    

    @classmethod
    def get_user(cls):
        from gws.model import User

        if cls._user is None:
            try:
                cls._user = User.get(User.token=="1234")
            except:
                cls._user = User(
                    token = "1234",
                    is_active = True
                )
                cls._user.save()
        
        return cls._user

    @classmethod
    def get_experiment(cls):
        from gws.model import Experiment

        if cls._experiment is None:
            cls._experiment = Experiment(
                user = cls.get_user(),
            )
            cls._experiment.save()
        
        return cls._experiment

class UserSession(Base):
    pass
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
                cls._user = User.get(User.email=="test@gencovery.com", User.organization=="Gencovery")
            except:
                cls._user = User(
                    firstname = "Guest", 
                    sirname = "Guest", 
                    email = "test@gencovery.com",
                    #password = "azerty123",
                    organization = "Gencovery",
                    is_active = True
                )
                cls._user.save()
        
        return cls._user

    @classmethod
    def get_project(cls):
        from gws.model import Project

        if cls._project is None:
            try:
                cls._project = Project.get(Project.name=="Test", Project.organization=="Gencovery")
            except:
                cls._project = Project(
                    name = "Test", 
                    organization = "Gencovery",
                    is_active = True,
                )
                cls._project.description = "This is a fake project for code testing."
                cls._project.save()
            
        return cls._project

    @classmethod
    def get_experiment(cls):
        from gws.model import Experiment

        if cls._experiment is None:
            cls._experiment = Experiment(
                user = cls.get_user(),
                project = cls.get_project()
            )
            cls._experiment.save()
        
        return cls._experiment
# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws.settings import Settings
from gws.model import Study, User, Experiment
from gws.controller import Controller

from gws.logger import Error

class GTest:
    user = None
    study = None
    
    @classmethod
    def init(cls):
        """
        This function initializes objects for unit testing
        """

        settings = Settings.retrieve()
        if not settings.is_test:
            raise Error("unittests", "init", "The unit tests can only be initialized in test mode")

        study = Study.get_default_instance()

        try:
            user = User.get(User.email=="test@gencovery.com")
            user.is_authenticated = True
        except:
            user = User(
                token="12345",
                email="test@gencovery.com",
                group="user",
                is_active=True,
                is_authenticated=True
            )

        user.save()
        #Controller.set_current_user(user)
        cls.user = user
        cls.study = study
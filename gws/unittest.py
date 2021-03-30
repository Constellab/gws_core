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
        User.create_owner_and_sysuser()
        user = User.get_sysuser()

        cls.user = user
        cls.study = study
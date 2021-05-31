# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws.settings import Settings
from gws.model import Study, User, Experiment
from gws.logger import Error

class GTest:
    user = None
    study = None
    tables = None
    
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
        User.authenticate(uri=user.uri, console_token=user.console_token) # refresh user information from DB
        
        cls.user = user
        cls.study = study
        
    @classmethod   
    def drop_tables(cls, models):
        """
        Drops a list of table associatied to object classes
        """
        for t in models:
            t.drop_table()

    @classmethod
    def print(cls, text):
        print("=======================================================")
        print(f" {text} ")
        print("=======================================================")
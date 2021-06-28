# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws.settings import Settings
from gws.model import Study, User, Experiment
from gws.logger import Error
from gws.service.model_service import ModelService

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
        if not settings.is_dev:
            raise Error("unittests", "init", "The unit tests can only be initialized in dev mode")

        study = Study.get_default_instance()
        User.create_owner_and_sysuser()
        user = User.get_sysuser()
        User.authenticate(uri=user.uri, console_token=user.console_token) # refresh user information from DB
        
        cls.user = user
        cls.study = study

    @classmethod
    def create_tables(cls, models: list = None):
        """
        Drops a list of table associatied to object classes
        """

        db_list, model_list = cls._get_db_and_model_lists(models)
        for db in db_list:
            i = db_list.index(db)
            models = [ t for t in model_list[i] if not t.table_exists() ]
            db.create_tables(models)

    @classmethod
    def drop_tables(cls, models = []):
        """
        Drops a list of table associatied to object classes
        """

        db_list, model_list = cls._get_db_and_model_lists(models) 
        for db in db_list:
            i = db_list.index(db)
            models = [ t for t in model_list[i] if t.table_exists() ]
            db.drop_tables(models)

    @classmethod
    def _get_db_and_model_lists(cls, models: list = None):
        if not models:
            models = ModelService._inspect_model_types()

        db_list = []
        model_list = []
        for t in models:
            db = t._db_manager.db
            if db in db_list:
                i = db_list.index(db)
                model_list[i].append(t)
            else:
                db_list.append(db)
                model_list.append([t])
        
        return db_list, model_list

    @classmethod
    def print(cls, text):
        print("\n*****************************************************")
        print(  "*")
        print( f"* {text} ")
        print(  "*")
        print(  "*****************************************************\n")
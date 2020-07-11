# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws.prism.model import Resource, ViewModel, DbManager
from gws.prism.view import ViewTemplateFile
from gws.settings import Settings
from peewee import ForeignKeyField

# ####################################################################
#
# Session class
#
# ####################################################################

class Session(Resource):

    class Meta:
        database = DbManager.db
        table_name = 'session'


# ####################################################################
#
# Session ViewModel class
#
# ####################################################################

class SessionViewModel(ViewModel):
    model: 'Resource' = ForeignKeyField(Session, backref='view_model')
    _table_name = 'session_view_model'

    def __init__(self, model_instance, *args, **kwargs):
        self.__init__(model_instance, *args, **kwargs)

        if self.template is None:
            settings = Settings()
            template_dir = settings.get_template_dir("gws")
            self.template = ViewTemplateFile(os.path.join(template_dir, "./prism/session/session.html"), type="html")

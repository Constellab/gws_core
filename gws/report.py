# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from peewee import ForeignKeyField
from gws.model import ViewModel, Viewable, Experiment

class Report(Viewable):
    experiment = ForeignKeyField(Experiment, backref="reports")
    _table_name = "gws_report"
    
    pass
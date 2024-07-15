

from peewee import ForeignKeyField

from gws_core.experiment.experiment import Experiment

from .shared_entity_info import SharedEntityInfo


class SharedExperiment(SharedEntityInfo):

    _table_name = 'gws_shared_experiment'

    entity: Experiment = ForeignKeyField(Experiment, backref="+", on_delete='CASCADE')

    class Meta:
        table_name = 'gws_shared_experiment'

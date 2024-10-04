

from peewee import ForeignKeyField

from gws_core.scenario.scenario import Scenario

from .shared_entity_info import SharedEntityInfo


class SharedScenario(SharedEntityInfo):

    _table_name = 'gws_shared_scenario'

    entity: Scenario = ForeignKeyField(Scenario, backref="+", on_delete='CASCADE')

    class Meta:
        table_name = 'gws_shared_scenario'

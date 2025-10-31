

from gws_core.scenario.scenario import Scenario
from peewee import ForeignKeyField

from .shared_entity_info import SharedEntityInfo


class SharedScenario(SharedEntityInfo):


    entity: Scenario = ForeignKeyField(Scenario, backref="+", on_delete='CASCADE')

    class Meta:
        table_name = 'gws_shared_scenario'
        is_table = True

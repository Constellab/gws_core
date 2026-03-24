from peewee import ForeignKeyField

from gws_core.core.service.front_service import FrontService
from gws_core.scenario.scenario import Scenario

from .shared_entity_info import SharedEntityInfo


class SharedScenario(SharedEntityInfo):
    entity: Scenario = ForeignKeyField(Scenario, backref="+", on_delete="CASCADE")

    def get_external_object_url(self) -> str | None:
        """Build the URL of the external scenario on the other lab."""
        if not self.lab:
            return None
        lab_front_url = self.lab.get_front_url()
        if not lab_front_url:
            return None
        return FrontService(lab_url=lab_front_url).get_scenario_url(self.external_id)

    class Meta:
        table_name = "gws_shared_scenario"
        is_table = True

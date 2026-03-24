from peewee import ForeignKeyField

from gws_core.core.service.front_service import FrontService
from gws_core.resource.resource_model import ResourceModel

from .shared_entity_info import SharedEntityInfo


class SharedResource(SharedEntityInfo):
    entity: ResourceModel = ForeignKeyField(ResourceModel, backref="+", on_delete="CASCADE")

    def get_external_object_url(self) -> str | None:
        """Build the URL of the external resource on the other lab."""
        if not self.lab:
            return None
        lab_front_url = self.lab.get_front_url()
        if not lab_front_url:
            return None
        return FrontService(lab_url=lab_front_url).get_resource_url(self.external_id)

    class Meta:
        table_name = "gws_shared_resource"
        is_table = True

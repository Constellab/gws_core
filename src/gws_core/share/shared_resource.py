from peewee import ForeignKeyField

from gws_core.resource.resource_model import ResourceModel

from .shared_entity_info import SharedEntityInfo


class SharedResource(SharedEntityInfo):
    entity: ResourceModel = ForeignKeyField(ResourceModel, backref="+", on_delete="CASCADE")

    class Meta:
        table_name = "gws_shared_resource"
        is_table = True

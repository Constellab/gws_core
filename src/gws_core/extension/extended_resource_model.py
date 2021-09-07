# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any
from peewee import Field, ForeignKeyField, ManyToManyField, ModelSelect
from ..core.model.json_field import JSONField
from ..resource.resource_model import ResourceModel
from ..model.typing_register_decorator import typing_registrator
#from .deferred_resource_field import DefferredResourceField

@typing_registrator(unique_name="ExtendedResourceModel", object_type="GWS_CORE", hide=True)
class ExtendedResourceModel(ResourceModel):
    """
    Extension to support models with extra db columns.

    Extra db columns are automatically synchronized with the resource if properties with same names are defined on the Resource.
    ForeignKeyFields and ManyToManyFields are not synchronized automatically because they generally require to be resolved manually.
    """

    @staticmethod
    def __process_field_value( value: Any ) -> Any:
        if isinstance(value, ResourceModel):
            value = value.get_resource()
        else:
            if isinstance(value, list):
                for k in range(0, len(value)):
                    if isinstance(value, ResourceModel):
                        value[k] = value[k].get_resource()
            elif isinstance(value, ModelSelect):
                # TODO: use DeferrefResourceField ...
                pass
            return value

    def send_fields_to_resource(self, resource, new_instance):
        super().send_fields_to_resource(resource, new_instance)
        # TODO : use DeferrefResourceField for  ForeignKeyField
        exclusion_list = (ForeignKeyField, JSONField, ManyToManyField, )
        prop_list = [
            *self.property_names(Field, exclude=exclusion_list),
            *self.property_method_names()
        ]
        for prop in prop_list:
            if not prop.startswith("_"):    # skip protected fields
                val = ExtendedResourceModel.__process_field_value( getattr(self, prop) )
                if hasattr(resource, prop): # synchronize existing fields declared on the resource
                    setattr(resource, prop, val)
                else:
                    pass
                    # TODO: add a param in the decorator to allow this behavior || or let it by default ?
                    #resource.__setattr__(prop, val) # create the resource field if it does not exists     

    def receive_fields_from_resource(self, resource):
        super().receive_fields_from_resource(resource)
        exclusion_list = (ForeignKeyField, JSONField, ManyToManyField, )
        prop_list = [
            *self.property_names(Field, exclude=exclusion_list),
            *self.property_method_names()
        ]
        for prop in prop_list:
            if not prop.startswith("_"):    # skip protected fields
                if hasattr(resource, prop): # only synchronize fields declared on the resource
                    val = ExtendedResourceModel.__process_field_value( getattr(resource, prop) )
                    setattr(self, prop, val)

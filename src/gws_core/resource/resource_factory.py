# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import copy
from typing import Any, Dict, Type

from gws_core.resource.kv_store import KVStore
from gws_core.resource.r_field.r_field import BaseRField
from gws_core.resource.resource import Resource


class ResourceFactory():
    """Factory to create a resource from type and data

    :return: _description_
    :rtype: _type_
    """

    @classmethod
    def create_resource(cls, resource_type: Type[Resource],
                        kv_store: KVStore, data: Dict[str, Any],
                        resource_model_id: str = None, name: str = None) -> Resource:
        resource: Resource = resource_type()

        if resource_model_id:
            # Pass the model id to the resource
            resource._model_id = resource_model_id

        if name:
            resource.name = name

        cls._send_fields_to_resource(resource, kv_store=kv_store, data=data)
        return resource

    @classmethod
    def _send_fields_to_resource(cls, resource: Resource,
                                 kv_store: KVStore, data: Dict[str, Any]) -> None:
        """for each BaseRField of the resource, set the value form the data or kvstore

        :param resource: [description]
        :type resource: ResourceType
        """

        properties: Dict[str, BaseRField] = resource.__get_resource_r_fields__()

        resource._kv_store = kv_store

        # for each BaseRField of the resource, set the value form the data or kvstore
        for key, r_field in properties.items():
            # If the property is searchable, it is stored in the DB
            if r_field.searchable:
                loaded_value = copy.deepcopy(r_field.deserialize(data.get(key)))
                setattr(resource, key, loaded_value)

            # if it comes from the kvstore, lazy load it
            elif kv_store is not None:
                # delete the RField default value so the lazy load can be called
                delattr(resource, key)



import copy
from typing import Any, Dict, List, Type

from pandas import DataFrame
from plotly.graph_objs import Figure

from gws_core.impl.json.json_dict import JSONDict
from gws_core.impl.plotly.plotly_resource import PlotlyResource
from gws_core.impl.table.table import Table
from gws_core.impl.text.text import Text
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.kv_store import KVStore
from gws_core.resource.r_field.r_field import BaseRField
from gws_core.resource.resource import Resource
from gws_core.resource.resource_set.resource_list import ResourceList
from gws_core.tag.tag import Tag


class ResourceFactory():
    """Factory to create a resource from type and data

    :return: _description_
    :rtype: _type_
    """

    @classmethod
    def create_resource(cls, resource_type: Type[Resource],
                        kv_store: KVStore, data: Dict[str, Any],
                        resource_model_id: str = None, name: str = None,
                        tags: List[Tag] = None,
                        style: TypingStyle = None) -> Resource:
        resource: Resource = resource_type()

        if resource_model_id:
            # Pass the model id to the resource
            resource._model_id = resource_model_id

        if name:
            resource.name = name

        if tags:
            resource.tags.add_tags(tags)

        if style:
            resource.style = style

        cls._send_fields_to_resource(resource, kv_store=kv_store, data=data)

        resource.init()
        return resource

    @classmethod
    def _send_fields_to_resource(cls, resource: Resource,
                                 kv_store: KVStore, data: Dict[str, Any]) -> None:
        """for each BaseRField of the resource, set the value form the data or kvstore

        :param resource: [description]
        :type resource: ResourceType
        """

        properties: Dict[str,
                         BaseRField] = resource.__get_resource_r_fields__()

        resource._kv_store = kv_store

        # for each BaseRField of the resource, set the value form the data or kvstore
        for key, r_field in properties.items():
            # If the property is searchable, it is stored in the DB
            if r_field.searchable:
                loaded_value = copy.deepcopy(
                    r_field.deserialize(data.get(key)))
                setattr(resource, key, loaded_value)

            # if it comes from the kvstore, lazy load it
            elif kv_store is not None:
                # delete the RField default value so the lazy load can be called
                delattr(resource, key)

    @classmethod
    def create_from_object(cls, resource: Any) -> Resource:
        """Create a resource based on object type.
        For example a Dataframe will be converted to a Table
        String to Text
        return None if the object could not be converted to a resource

        :param resource: _description_
        :type resource: Any
        :return: _description_
        :rtype: Resource
        """
        if resource is None:
            return None

        if isinstance(resource, Resource):
            return resource

        if isinstance(resource, str):
            return Text(resource)
        if isinstance(resource, dict):
            return JSONDict(resource)
        if isinstance(resource, list):
            return ResourceList([cls.create_from_object(r) for r in resource])
        if isinstance(resource, DataFrame):
            return Table(resource)
        if isinstance(resource, Figure):
            return PlotlyResource(resource)

        return None

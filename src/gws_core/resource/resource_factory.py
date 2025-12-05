import copy
from typing import Any, cast

from pandas import DataFrame
from plotly.graph_objs import Figure

from gws_core.impl.json.json_dict import JSONDict
from gws_core.impl.plotly.plotly_resource import PlotlyResource
from gws_core.impl.table.table import Table
from gws_core.impl.text.text import Text
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.kv_store import KVStore
from gws_core.resource.r_field.r_field import BaseRField, RFieldStorage
from gws_core.resource.resource import Resource
from gws_core.resource.resource_set.resource_list import ResourceList
from gws_core.tag.tag import Tag


class ResourceFactory:
    """Factory to create a resource from type and data.

    This factory handles the creation and initialization of Resource objects,
    including loading field values from different storage backends based on RFieldStorage settings.
    """

    @classmethod
    def create_resource(
        cls,
        resource_type: type[Resource],
        kv_store: KVStore,
        data: dict[str, Any],
        resource_model_id: str | None = None,
        name: str | None = None,
        tags: list[Tag] | None = None,
        flagged: bool = False,
        style: TypingStyle | None = None,
        additional_data: dict[str, Any] | None = None,
    ) -> Resource:
        """Creates and initializes a Resource instance with data from various storage backends.

        :param resource_type: The class type of the resource to create
        :type resource_type: Type[Resource]
        :param kv_store: Key-value store instance for loading RFields with KV_STORE storage
        :type kv_store: KVStore
        :param data: Dictionary containing values for RFields with DATABASE storage
        :type data: Dict[str, Any]
        :param resource_model_id: Optional model ID to assign to the resource, defaults to None
        :type resource_model_id: str | None, optional
        :param name: Optional name for the resource, defaults to None
        :type name: str | None, optional
        :param tags: Optional list of tags to apply to the resource, defaults to None
        :type tags: List[Tag] | None, optional
        :param flagged: Whether the resource should be flagged, defaults to False
        :type flagged: bool, optional
        :param style: Optional typing style to apply to the resource, defaults to None
        :type style: TypingStyle | None, optional
        :param additional_data: Dictionary containing values for RFields with NONE storage (transient data), defaults to None
        :type additional_data: Dict[str, Any] | None, optional
        :return: The created and initialized resource instance
        :rtype: Resource
        """
        resource: Resource = resource_type()

        if resource_model_id:
            # Pass the model id to the resource
            resource.__set_model_id__(resource_model_id)

        if name:
            resource.name = name

        if tags:
            resource.tags.add_tags(tags)

        if style:
            resource.style = style

        resource.flagged = flagged

        cls._send_fields_to_resource(
            resource, kv_store=kv_store, data=data, additional_data=additional_data
        )

        resource.init()
        return resource

    @classmethod
    def _send_fields_to_resource(
        cls,
        resource: Resource,
        kv_store: KVStore,
        data: dict[str, Any],
        additional_data: dict[str, Any] | None = None,
    ) -> None:
        """Populates resource RFields from appropriate storage backends based on their RFieldStorage setting.

        This method iterates through all RFields of the resource and loads their values from the
        appropriate storage backend:
        - DATABASE storage: values loaded from the 'data' dictionary
        - KV_STORE storage: values lazy-loaded from the key-value store
        - NONE storage: values loaded from 'additional_data' if provided, otherwise default value is kept

        :param resource: The resource instance to populate
        :type resource: Resource
        :param kv_store: Key-value store instance for lazy-loading RFields with KV_STORE storage
        :type kv_store: KVStore
        :param data: Dictionary containing values for RFields with DATABASE storage (from database)
        :type data: Dict[str, Any]
        :param additional_data: Dictionary containing values for RFields with NONE storage (transient data), defaults to None
        :type additional_data: Dict[str, Any] | None, optional
        """

        properties: dict[str, BaseRField] = resource.__get_resource_r_fields__()

        resource.__set_kv_store__(kv_store)

        # for each BaseRField of the resource, set the value from the appropriate storage
        for key, r_field in properties.items():
            # If the storage is DATABASE, the value is stored in the DB
            if r_field.storage == RFieldStorage.DATABASE:
                loaded_value = copy.deepcopy(r_field.deserialize(data.get(key)))
                setattr(resource, key, loaded_value)

            # If the storage is KV_STORE, lazy load it from the kv store
            elif r_field.storage == RFieldStorage.KV_STORE:
                # delete the RField default value so the lazy load can be called
                delattr(resource, key)

            # If the storage is NONE, get the value from additional_data
            elif r_field.storage == RFieldStorage.NONE:
                if additional_data and key in additional_data:
                    loaded_value = copy.deepcopy(r_field.deserialize(additional_data.get(key)))
                    setattr(resource, key, loaded_value)
                # Otherwise keep the default value (do nothing)

    @classmethod
    def create_from_object(cls, resource: Any) -> Resource | None:
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
            resources_list = cast(
                list[Resource], [cls.create_from_object(r) for r in resource if r is not None]
            )
            return ResourceList(resources_list)
        if isinstance(resource, DataFrame):
            return Table(resource)
        if isinstance(resource, Figure):
            return PlotlyResource(resource)

        return None

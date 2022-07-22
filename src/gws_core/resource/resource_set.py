# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, Set

from gws_core.resource.r_field.dict_r_field import DictRField
from gws_core.resource.resource_list_base import ResourceListBase

from .resource import Resource
from .resource_decorator import resource_decorator


@resource_decorator(unique_name="ResourceSet", human_name="Resource set",
                    short_description="A set of resources")
class ResourceSet(ResourceListBase):
    """Resource to manage a set of resources. By default the sytem create a new
    resource for each resource in the set when saving the set
    """

    # dict where key is the initial name of the resource and value is the resource id
    _resource_ids: Dict[str, str] = DictRField()

    # dict provided before the resources are saved
    _resources: Dict[str, Resource] = None

    def get_resources(self) -> Dict[str, Resource]:
        if not self._resources:
            resources = self._load_resources()
            self._resources = {}
            for resource_name, id in self._resource_ids.items():
                # search the resource with same id and set it in _resources
                for resource in resources:
                    if resource._model_id == id:
                        self._resources[resource_name] = resource
                        break

        return self._resources

    def _get_resource_ids(self) -> Set[str]:
        return set(self._resource_ids.values())

    def get_resources_as_set(self) -> Set[Resource]:
        return set(self.get_resources().values())

    def _set_r_field(self) -> None:
        """ set _resource_ids with key = resource_name and value = resource_id"""
        self._resource_ids = {name: resource._model_id for name, resource in self._resources.items()}

    def add_resource(self, resource: Resource,
                     unique_name: str = None,
                     create_new_resource: bool = True) -> None:
        """Add a resource to the set

        :param resource: resource to Add
        :type resource: Resource
        :param unique_name: name used to store the resource in the dict. It must be unique. The resource
        can be retrieve by calling the get_resource method with the name. If not provided, the resource name is used
        :type unique_name: str
        :param create_new_resource: If true, a new resource is created when saving the resource.
                                    Otherwise it doesn't create a new resource but references it. In this case
                                    the resource must be an input of the task that created the ResourceSet and the resource
                                    must have been saved before, defaults to True
        :type create_new_resource: bool, optional
        """
        if not isinstance(resource, Resource):
            raise Exception('The resource_set only takes set of resources')

        if isinstance(resource, ResourceListBase):
            raise Exception('ResourceSet does not support nested')

        if self._model_id is not None:
            raise Exception("The ResourceSet is already saved, you can't add a resource to it")

        if not create_new_resource and resource._model_id is None:
            raise Exception("The resource must be saved before, if you use the create_new_resource option")

        if self._resources is None:
            self._resources = {}

        name = unique_name or resource.name
        if name is None:
            raise Exception('The unique name was not provided and the resource name is not set')
        if name in self._resources:
            raise Exception(f'Resource with name {name} already exists')

        # if the resource already exist, add it to the constant list so
        # the system will not create a new resource on save
        if not create_new_resource:
            if self.__constant_resource_ids__ is None:
                self.__constant_resource_ids__ = set()
            self.__constant_resource_ids__.add(resource.uid)

        self._resources[name] = resource

    def get_resource(self, resource_name: str) -> Resource:
        resources = self.get_resources()

        if not resource_name in resources:
            raise Exception('Resource name is not set')

        return resources[resource_name]

    def resource_exists(self, resource_name: str) -> Resource:
        resources = self.get_resources()
        return resource_name in resources

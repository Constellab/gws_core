from gws_core.resource.r_field.dict_r_field import DictRField

from ..resource import Resource
from ..resource_decorator import resource_decorator
from .resource_list_base import ResourceListBase


@resource_decorator(
    unique_name="ResourceSet", human_name="Resource set", short_description="A set of resources"
)
class ResourceSet(ResourceListBase):
    """Resource to manage a set of resources. By default the sytem create a new
    resource for each resource in the set when saving the set
    """

    # dict where key is the initial name of the resource and value is the resource model id
    _resource_ids: dict[str, str] = DictRField()

    # dict provided before the resources are saved
    _resources: dict[str, Resource] = None

    def get_resources(self) -> dict[str, Resource]:
        """
        Return the sub resources as a dict

        :return: dict of resources where key is the resource name
        :rtype: Dict[str, Resource]
        """
        if not self._resources:
            resources = self._load_resources()
            self._resources = {}
            for resource_name, id_ in self._resource_ids.items():
                # search the resource with same id and set it in _resources
                for resource in resources:
                    if resource.get_model_id() == id_:
                        self._resources[resource_name] = resource
                        break

        return self._resources

    def get_resource_model_ids(self) -> set[str]:
        """
        Return the resource model ids of the sub resources

        :return: set of resource model ids
        :rtype: Set[str]
        """
        return set(self._resource_ids.values())

    def get_resources_as_set(self) -> set[Resource]:
        """
        Return the sub resources as a set

        :return: set of resources
        :rtype: Set[Resource]
        """
        return set(self.get_resources().values())

    def __set_r_field__(self, saved_resources: dict[str, Resource]) -> None:
        resources_dict = {}
        resource_ids = {}
        for key, existing_resource in self._resources.items():
            if existing_resource.uid not in saved_resources:
                raise Exception(
                    f"The resource with uid '{existing_resource.uid}' was not found in the saved resources"
                )
            new_resource = saved_resources[existing_resource.uid]
            resources_dict[key] = new_resource
            resource_ids[key] = new_resource.get_model_id()

        self._resource_ids = resource_ids
        self._resources = resources_dict

    def add_resource(
        self, resource: Resource, unique_name: str | None = None, create_new_resource: bool = True
    ) -> None:
        """Add a resource to the set

        :param resource: resource to add
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
        self._check_resource_before_add(resource)

        # load the existing resources
        resources = self.get_resources()
        if resources is None:
            self._resources = {}

        name = unique_name or resource.name
        if name is None:
            raise Exception("The unique name was not provided and the resource name is not set")

        if name in resources:
            raise Exception(f"Resource with name '{name}' already exists in the ResourceSet")

        # if the resource already exist, add it to the constant list so
        # the system will not create a new resource on save
        if not create_new_resource:
            self._mark_resource_as_constant(resource)

        self._resources[name] = resource

    def get_resource(self, resource_name: str) -> Resource:
        """
        Return the resource with the given name

        :param resource_name: name of the resource
        :type resource_name: str
        :raises Exception: if the resource with the given name is not found
        :return: resource with the given name
        :rtype: Resource
        """

        resources = self.get_resources()

        if resource_name not in resources:
            raise Exception(f"Resource with name {resource_name} not found")

        return resources[resource_name]

    def get_resource_or_none(self, resource_name: str) -> Resource | None:
        """
        Return the resource with the given name or None if not found

        :param resource_name: name of the resource
        :type resource_name: str
        :return: resource with the given name or None if not found
        :rtype: Resource | None
        """
        resources = self.get_resources()
        return resources.get(resource_name, None)

    def resource_exists(self, resource_name: str) -> Resource:
        """
        Return true if the resource with the given name exists in the dict

        :param resource_name: name of the resource
        :type resource_name: str
        :return: True if the resource with the given name exists in the dict
        :rtype: Resource
        """
        resources = self.get_resources()
        return resource_name in resources

    def clear_resources(self) -> None:
        """
        Clear the resources
        """
        self._resources = {}
        self._resource_ids = {}
        self.__constant_resource_model_ids__ = set()

    def replace_resources_by_model_id(self, resources: dict[str, Resource]) -> None:
        """
        Replace current resources by the resources in the dict

        :param resources: dict where key is the resource model id and value is the resource
        :type resources: Dict[str, Resource]
        """

        # get a copy of the original dict to iterate over it
        resource_ids = self._resource_ids

        self.clear_resources()

        for name, resource_model_id in resource_ids.items():
            if resource_model_id not in resources:
                raise Exception(
                    f"Resource with id {resource_model_id} not found in the resources to replace"
                )
            self.add_resource(resources[resource_model_id], unique_name=name)

    def __len__(self) -> int:
        return len(self.get_resources())

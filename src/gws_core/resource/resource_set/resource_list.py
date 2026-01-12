from gws_core.resource.r_field.list_r_field import ListRField

from ..resource import Resource
from ..resource_decorator import resource_decorator
from .resource_list_base import ResourceListBase


@resource_decorator(
    unique_name="ResourceList",
    human_name="Resource list",
    short_description="A list of resources",
    hide=True,
)
class ResourceList(ResourceListBase):
    """Resource to manage a list of resources. By default the sytem create a new
    resource for each resource in the set when saving the set

    """

    # list of resource ids stored
    _resource_ids: list[str] = ListRField()

    # dict provided before the resources are saved
    _resources: list[Resource]

    def __init__(self, resources: list[Resource] | None = None):
        super().__init__()
        self._resources = resources or []

    def get_resources(self) -> list[Resource]:
        """
        Return the sub resources as a list

        :return: list of resources
        :rtype: List[Resource]
        """

        if not self._resources:
            # load the resource and keep the _resources order
            resources = []
            for resource_id in self._resource_ids:
                resources.append(self._get_resource_by_model_id(resource_id))
            self._resources = resources

        return self._resources

    def get_resource_model_ids(self) -> set[str]:
        """
        Return the resource model ids of the sub resources

        :return: set of resource model ids
        :rtype: Set[str]
        """
        return set(self._resource_ids)

    def get_resources_as_set(self) -> set[Resource]:
        """
        Return the sub resources as a set

        :return: set of resources
        :rtype: Set[Resource]
        """
        return set(self.get_resources())

    def get_resource_by_name(self, name: str) -> Resource | None:
        """
        Return the first resource with the given name

        :param name: name of the resource
        :type name: str
        :return: resource
        :rtype: Resource
        """
        for resource in self.get_resources():
            if resource.name == name:
                return resource
        return None

    def __set_r_field__(self, saved_resources: dict[str, Resource]) -> None:
        resources_list = []
        resource_ids = []
        for existing_resource in self._resources:
            if existing_resource.uid not in saved_resources:
                raise Exception(
                    f"The resource with uid '{existing_resource.uid}' was not found in the saved resources"
                )
            new_resource = saved_resources[existing_resource.uid]
            resources_list.append(new_resource)
            resource_ids.append(new_resource.get_model_id())

        self._resources = resources_list
        self._resource_ids = resource_ids

    def add_resource(self, resource: Resource, create_new_resource: bool = True) -> None:
        """Add a resource to the list

        :param resource: resource to add
        :type resource: Resource
        :param create_new_resource: If true, a new resource is created when saving the resource.
                                    Otherwise it doesn't create a new resource but references it. In this case
                                    the resource must be an input of the task that created the ResourceList and the resource
                                    must have been saved before, defaults to True
        :type create_new_resource: bool, optional
        """
        self._check_resource_before_add(resource)
        # if the resource already exist, add it to the constant list so
        # the system will not create a new resource on save
        if not create_new_resource:
            self._mark_resource_as_constant(resource)

        # load the existing resources
        resources = self.get_resources()
        if resources is None:
            self._resources = []
        self._resources.append(resource)

    def clear_resources(self) -> None:
        self._resources = []
        self._resource_ids = []
        self.__constant_resource_model_ids__ = set()

    def to_list(self) -> list[Resource]:
        """
        Return the resources as a list

        :return: list of resources
        :rtype: List[Resource]
        """
        return self.get_resources()

    def is_empty(self) -> bool:
        """
        Return true if the resource list is empty

        :return: True if the resource list is empty
        :rtype: bool
        """
        return len(self.get_resources()) == 0

    def replace_resources_by_model_id(self, resources: dict[str, Resource]) -> None:
        """
        Replace current resources by the resources in the dict

        :param resources: dict where key is the resource model id and value is the resource
        :type resources: Dict[str, Resource]
        """

        # get a copy of original order to replace resources in the same order
        original_order = self._resource_ids

        self.clear_resources()

        for resource_model_id in original_order:
            if resource_model_id not in resources:
                raise Exception(
                    f"Resource with id {resource_model_id} not found in the resources to replace"
                )
            self.add_resource(resources[resource_model_id])

    # add methods to act like a list

    def __getitem__(self, key) -> Resource:
        return self.get_resources()[key]

    def __setitem__(self, key, val: Resource) -> None:
        self.get_resources()[key] = val

    def __len__(self) -> int:
        return len(self.get_resources())

    def __iter__(self):
        return iter(self.get_resources())

    def __contains__(self, item) -> bool:
        return item in self.get_resources()

    def index(self, item) -> int:
        return self.get_resources().index(item)

    def count(self, item) -> int:
        return self.get_resources().count(item)

    def sort(self, key=None, reverse=False) -> None:
        self.get_resources().sort(key=key, reverse=reverse)

    def reverse(self) -> None:
        self.get_resources().reverse()

    def clear(self) -> None:
        self.get_resources().clear()

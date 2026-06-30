from typing import TypeVar, overload

from ..resource.resource import Resource

# Type for the output of a task
TaskOutputs = dict[str, Resource | None]

ResourceType = TypeVar("ResourceType", bound="Resource")


class TaskInputs(dict[str, Resource | None]):
    """Class wrapping all the inputs of a task

    :param Dict: [description]
    :type Dict: [type]
    """

    def has_resource(self, name: str) -> bool:
        """Returns true if the resource with the name exists and is set"""
        return name in self and self[name] is not None

    @overload
    def get_resource(self, name: str) -> Resource | None: ...

    @overload
    def get_resource(self, name: str, resource_type: type[ResourceType]) -> ResourceType: ...

    def get_resource(
        self, name: str, resource_type: type[ResourceType] | None = None
    ) -> Resource | ResourceType | None:
        """Retrieve the resource of the input.

        :param name: name of the input port
        :type name: str
        :param resource_type: if provided, check that the resource is of this type and return it as this type
        :type resource_type: type[Resource] | None
        :return: resource of the input, or None if the input is empty
        :rtype: Resource | None
        """
        resource = self.get(name)

        if resource is None:
            if resource_type is not None:
                raise Exception(
                    f"The input '{name}' is empty, expected a resource of type '{resource_type.__name__}'"
                )
            return None

        if resource_type is not None and not isinstance(resource, resource_type):
            raise Exception(
                f"The input '{name}' is of type '{type(resource).__name__}', expected '{resource_type.__name__}'"
            )

        return resource

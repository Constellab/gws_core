

from typing import Dict

from ..resource.resource import Resource

# Type for the output of a task
TaskOutputs = Dict[str, Resource]


class TaskInputs(Dict[str, Resource]):
    """Class wrapping all the inputs of a task

    :param Dict: [description]
    :type Dict: [type]
    """

    def has_resource(self, name: str) -> bool:
        """Returns true if the resource with the name exists and is set
        """
        return name in self and self[name] is not None

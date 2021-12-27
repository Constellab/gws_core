# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Dict, List

from ...core.classes.jsonable import Jsonable, ListJsonable
from ...task.task_typing import TaskTyping


class ResourceImportersDTO(Jsonable):
    """DTO to get the list of importer for a resource type and it's parent types.

    Importer are grouped by type

    :return: [description]
    :rtype: [type]
    """

    resource: TaskTyping
    importers: List[TaskTyping]

    def __init__(self, resource: TaskTyping) -> None:
        self.resource = resource
        self.importers = []

    def add_importer(self, importer: TaskTyping) -> None:
        self.importers.append(importer)

    def to_json(self) -> Dict:
        return {
            "resource": self.resource.to_json(),
            "importers": ListJsonable(self.importers).to_json(deep=True)
        }

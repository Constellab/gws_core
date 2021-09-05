# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Type
from ..resource.resource import Resource
from ..resource.resource_model import ResourceModel

class DefferredResourceField:
    resource_model_uri: str
    resource_model_type: Type[ResourceModel]

    def __init__(self, resource_model: ResourceModel):
        self.resource_model_uri = resource_model.uri
        self.resource_model_type = type(resource_model)

    def fetch(self) -> Resource:
        resource_model_type = self.resource_model_type
        resource_model_instance: ResourceModel = resource_model_type.get( resource_model_type.uri == self.resource_model_uri )
        return resource_model_instance.get_resource()

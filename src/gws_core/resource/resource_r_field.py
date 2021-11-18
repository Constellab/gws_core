
from typing import TypedDict, final

from gws_core.model.typing_manager import TypingManager
from gws_core.resource.resource_model import ResourceModel

from .r_field import BaseRField
from .resource import Resource


@final
class ResourceRField(BaseRField):

    def __init__(self) -> None:
        super().__init__(searchable=True, default_value=None, include_in_dict_view=False)

    def deserialize(self, resource_model_id: str) -> Resource:
        if resource_model_id is None:
            return None

        resource_model: ResourceModel = ResourceModel.get_by_id_and_check(resource_model_id)

        return resource_model.get_resource()

    def serialize(self, r_field_value: Resource) -> str:
        if r_field_value is None:
            return None
        if not isinstance(r_field_value, Resource):
            raise Exception(
                f"The value passed to the ResourceRField is not a ressource but a '{str(type(r_field_value))}'")

        if r_field_value._model_id is None:
            raise Exception(
                f"Only a resource previously saved can be passed to a ResourceRField. It must have been the output of a previous task")

        return r_field_value._model_id

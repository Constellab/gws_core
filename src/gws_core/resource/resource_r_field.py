import warnings
from typing import final

from .r_field.r_field import BaseRField, RFieldStorage
from .resource import Resource
from .resource_model import ResourceModel


@final
class ResourceRField(BaseRField):
    """RField, these fields must be used in resource attribute
    This field is useful to link a resource with another resource without duplicating them.
    When the resource is saved after a task, the field must contains a Resource and if yes, this resource
    will be linked with the generated resource. Next time this resource is instantiated, the linked resource will be
    provided in the ResourceRField.

    //!\\ WARNING: the linked resource MUST be a resource provided as input of the task that generate
    the resource marked with ResourceRField. Otherwise there will be an error before saving the generated resource because it can
    break the tracability of resources

    .. deprecated::
        ResourceRField is deprecated and will be removed in a future version.
        Please consider alternative approaches for resource linking.
    """

    def __init__(self) -> None:
        warnings.warn(
            "ResourceRField is deprecated and will be removed in a future version. "
            "Please dfine a sub class of ResourceSet instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(
            default_value=None, include_in_dict_view=False, storage=RFieldStorage.DATABASE
        )

    def deserialize(self, r_field_value: str) -> Resource:
        if r_field_value is None:
            return None

        resource_model: ResourceModel = ResourceModel.get_by_id_and_check(r_field_value)

        return resource_model.get_resource()

    def serialize(self, r_field_value: Resource) -> str:
        if r_field_value is None:
            return None
        if not isinstance(r_field_value, Resource):
            raise Exception(
                f"The value passed to the ResourceRField is not a ressource but a '{str(type(r_field_value))}'"
            )

        if r_field_value.get_model_id() is None:
            raise Exception(
                "Only a resource previously saved can be passed to a ResourceRField. It must have been the output of a previous task"
            )

        return r_field_value.get_model_id()

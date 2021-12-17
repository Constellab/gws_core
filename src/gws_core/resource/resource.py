
from typing import Dict

from ..config.config_types import ConfigParams
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..core.model.base import Base
from ..core.utils.reflector_helper import ReflectorHelper
from ..impl.json.json_view import JSONView
from ..model.typing_register_decorator import typing_registrator
from ..resource.r_field import BaseRField, UUIDRField
from ..resource.view_decorator import view

# Typing names generated for the class resource
CONST_RESOURCE_TYPING_NAME = "RESOURCE.gws_core.Resource"


@typing_registrator(unique_name="Resource", object_type="RESOURCE")
class Resource(Base):

    uid: str = UUIDRField(searchable=True)

    # Provided at the Class level automatically by the @ResourceDecorator
    # //!\\ Do not modify theses values
    _typing_name: str = None
    _human_name: str = None
    _short_description: str = None
    _model_id: str = None

    def __init__(self):
        # check that the class level property _typing_name is set
        if self._typing_name == CONST_RESOURCE_TYPING_NAME and type(self) != Resource:  # pylint: disable=unidiomatic-typecheck
            raise BadRequestException(
                f"The resource {self.full_classname()} is not decorated with @ResourceDecorator, it can't be instantiate. Please decorate the resource class with @ResourceDecorator")

        # Init default values of BaseRField
        properties: Dict[str, BaseRField] = ReflectorHelper.get_property_names_of_type(type(self), BaseRField)
        for key, r_field in properties.items():
            setattr(self, key, r_field.get_default_value())

    # -- G --

    @view(view_type=JSONView, human_name="View as JSON", short_description="View the complete resource as json", default_view=True)
    def view_as_json(self, params: ConfigParams) -> JSONView:
        """By default the view_as_json dumps the RFields mark with, include_in_dict_view=True
        This method is used to send the resource information back to the interface
        """
        properties: Dict[str, BaseRField] = ReflectorHelper.get_property_names_of_type(type(self), BaseRField)

        json_: dict = {}
        for key, r_field in properties.items():
            if r_field.include_in_dict_view:
                json_[key] = r_field.serialize(getattr(self, key))

        return JSONView(json_)

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Resource):
            return False
        return (self is o) or ((self.uid is not None) and (self.uid == o.uid))

    def get_name(self) -> str:
        """You can redefine this method to set a name of the resource.
        When saving the resource the name will be saved automatically
        This can be useful to distinguish this resource from another one or to search for the resource

        :return: [description]
        :rtype: [type]
        """
        return None

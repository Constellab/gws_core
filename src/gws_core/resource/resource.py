# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from copy import deepcopy
from typing import Dict, List, Union, final

from gws_core.resource.kv_store import KVStore
from gws_core.tag.tag import Tag

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
    name: str

    # provide tags to this attribute to save them on resource generation
    tags: Dict[str, str] = {}

    # Provided at the Class level automatically by the @ResourceDecorator
    # //!\\ Do not modify theses values
    _typing_name: str = None
    _human_name: str = None
    _short_description: str = None
    _is_exportable: bool = False
    # Set by the resource parent on creation
    _model_id: str = None
    _kv_store: KVStore = None

    def __init__(self):
        """Resource constructor
        /!\ It must have only optional parameters
        """

        # check that the class level property _typing_name is set
        if self._typing_name == CONST_RESOURCE_TYPING_NAME and type(self) != Resource:  # pylint: disable=unidiomatic-typecheck
            raise BadRequestException(
                f"The resource {self.full_classname()} is not decorated with @ResourceDecorator, it can't be instantiate. Please decorate the resource class with @ResourceDecorator")

        # init the default name
        self.name = None
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

    def __hash__(self):
        return hash(self.uid)

    def get_default_name(self) -> str:
        """You can redefine this method to set a name of the resource.
        When saving the resource the name will be saved automatically
        This can be useful to distinguish this resource from another one or to search for the resource

        :return: [description]
        :rtype: [type]
        """
        return self._human_name

    def check_resource(self) -> Union[str, None]:
        """You can redefine this method to define custom logic to check this resource.
        If there is a problem with the resource, return a string that define the error, otherwise return None
        This method is called on output resources of a task. If there is an error returned, the task will be set to error and next proceses will not be run.
        It is also call when uploading a resource (usually for files or folder), if there is an error returned, the resource will not be uploaded
        """
        return None

    def clone(self) -> 'Resource':
        """Clone the resource to create a new instance with a new id
            It copies the RFields
        """
        clone: Resource = type(self)()
        clone._model_id = self._model_id

        # get the r_fields of the resource
        r_fields: Dict[str, BaseRField] = self.__get_resource_r_fields__()
        for fieldname, r_field in r_fields.items():
            value = getattr(self, fieldname)
            setattr(clone, fieldname, deepcopy(value))

        return clone

    @ final
    @ classmethod
    def __get_resource_r_fields__(cls) -> Dict[str, BaseRField]:
        """Get the list of resource's r_fields,
        the key is the property name, the value is the BaseRField object
        """
        return ReflectorHelper.get_property_names_of_type(cls, BaseRField)

    @ final
    def __getattribute__(self, name):
        """Override get attribute to lazy load kvstore Rfields

        :param name: [description]
        :type name: [type]
        :return: [description]
        :rtype: [type]
        """
        attr = super().__getattribute__(name)

        if isinstance(attr, BaseRField):
            if name in self._kv_store:
                value = attr.deserialize(self._kv_store.get(name))
                setattr(self, name, value)
                return value
            else:
                # if the key is not in the kv_store return the default
                # this can happend when the RField is new
                return attr.get_default_value()

        return attr

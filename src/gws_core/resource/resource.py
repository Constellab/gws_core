from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any, Dict, Type

from gws_core.core.utils.utils import Utils
from gws_core.resource.r_field import BaseRField, UUIDRField

from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..core.model.base import Base
from ..model.typing_register_decorator import typing_registrator

if TYPE_CHECKING:
    from .resource_model import ResourceModel

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
    _model_uri: str = None

    def __init__(self):
        # check that the class level property _typing_name is set
        if self._typing_name == CONST_RESOURCE_TYPING_NAME and type(self) != Resource:  # pylint: disable=unidiomatic-typecheck
            raise BadRequestException(
                f"The resource {self.full_classname()} is not decorated with @ResourceDecorator, it can't be instantiate. Please decorate the resource class with @ResourceDecorator")

        # Init default values of BaseRField
        properties: Dict[str, BaseRField] = Utils.get_property_names_with_type(type(self), BaseRField)
        for key, r_field in properties.items():
            setattr(self, key, r_field.get_default_value())

    def export_to_path(self, file_path: str, file_format: str = None):
        """
        Export the resource to a repository

        :param file_path: The destination file path
        :type file_path: str
        """

        # @ToDo: ensure that this method is only called by an Exporter
        # TOdO do we need this ?

    # -- G --

    # TODO: add method get(), select() to fetch de model from DB and return correspondin resource
    # def select( predicat ):
    #     model = self.
    #     pass

    # -- I --

    @classmethod
    def import_from_path(cls, file_path: str, file_format: str = None) -> Any:
        """
        Import a resource from a repository. Must be overloaded by the child class.

        :param file_path: The source file path
        :type file_path: str
        :returns: the parsed data
        :rtype any
        """

        # @ToDo: ensure that this method is only called by an Importer

    def view_as_dict(self) -> Dict:
        """By default the view_as_dict dumps the RFields mark with, include_in_dict_view=True
        This method is used to send the resource information back to the interface
        """
        properties: Dict[str, BaseRField] = Utils.get_property_names_with_type(type(self), BaseRField)

        json_: dict = {}
        for key, r_field in properties.items():
            if r_field.include_in_dict_view:
                json_[key] = r_field.serialize(getattr(self, key))

        return json_

    # -- T --

    @classmethod
    def get_resource_model_type(cls) -> Type[ResourceModel]:
        """Return the resource model associated with this Resource
        //!\\ To overwrite only when you know what you are doing

        :return: [description]
        :rtype: Type[Any]
        """
        from .resource_model import ResourceModel
        return ResourceModel

    # -- V --

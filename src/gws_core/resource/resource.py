from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Type

from gws_core.resource.kv_store import KVStore

from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..core.model.base import Base
from ..model.typing_register_decorator import typing_registrator

if TYPE_CHECKING:
    from .resource_model import ResourceModel

# Typing names generated for the class Process
CONST_RESOURCE_TYPING_NAME = "RESOURCE.gws_core.Resource"


# Format of the serialized data of a resource to save data in the DB
SerializedResourceData = Dict


@typing_registrator(unique_name="Resource", object_type="RESOURCE")
class Resource(Base):

    # To store big data. This will be store in a file on the server. It will not be searchable
    kv_store: KVStore

    # Provided at the Class level automatically by the @ResourceDecorator
    # //!\\ Do not modify theses values
    _typing_name: str = None
    _human_name: str = None
    _short_description: str = None

    def __init__(self):
        # check that the class level property _typing_name is set
        if self._typing_name == CONST_RESOURCE_TYPING_NAME and type(self) != Resource:  # pylint: disable=unidiomatic-typecheck
            raise BadRequestException(
                f"The resource {self.full_classname()} is not decorated with @ResourceDecorator, it can't be instantiate. Please decorate the process class with @ResourceDecorator")

    @abstractmethod
    def serialize_data(self) -> SerializedResourceData:
        """Method to override to serialize the resource to save it

        Return small data of the resource store in the database. This dictionnary must not be to big/
        Information in the light data will be searchable  with a full text search

        :return: [description]
        :rtype: ResourceSerialized
        """

    @abstractmethod
    def deserialize_data(self, data: SerializedResourceData) -> None:
        """Method call after resource creation to init resource data

        Small data of the resource store in the database. This dictionnary must not be to big/
        Information in the light data will be searchable  with a full text search

        :param data: [description]
        :type data: SerializedResourceData
        """

    def export(self, file_path: str, file_format: str = None):
        """
        Export the resource to a repository

        :param file_path: The destination file path
        :type file_path: str
        """

        # @ToDo: ensure that this method is only called by an Exporter
        # TOdO do we need this ?

    # -- G --

    # -- I --

    @classmethod
    def import_resource(cls, file_path: str, file_format: str = None) -> Any:
        """
        Import a resource from a repository. Must be overloaded by the child class.

        :param file_path: The source file path
        :type file_path: str
        :returns: the parsed data
        :rtype any
        """

        # @ToDo: ensure that this method is only called by an Importer

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

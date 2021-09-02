from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Type

from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..core.model.base import Base
from ..model.typing_register_decorator import TypingDecorator
from .kv_store import KVStore
from .resource_data import ResourceData
from .resource_serialized import ResourceSerialized

if TYPE_CHECKING:
    from .resource_model import ResourceModel

# Typing names generated for the class Process
CONST_RESOURCE_TYPING_NAME = "RESOURCE.gws_core.Resource"


@TypingDecorator(unique_name="Resource", object_type="RESOURCE")
class Resource(Base):

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
    def serialize(self) -> ResourceSerialized:
        """Method to override to serialize the resource to save it

        :return: [description]
        :rtype: ResourceSerialized
        """
        pass

    @abstractmethod
    def deserialize(self, resource_serialized: ResourceSerialized) -> None:
        """Method call after resource creation to init resource data

        :param resource_serialized: [description]
        :type resource_serialized: ResourceSerialized
        """
        pass

    def export(self, file_path: str, file_format: str = None):
        """
        Export the resource to a repository

        :param file_path: The destination file path
        :type file_path: str
        """

        # @ToDo: ensure that this method is only called by an Exporter
        # TOdO do we need this ?

        pass

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

        pass

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

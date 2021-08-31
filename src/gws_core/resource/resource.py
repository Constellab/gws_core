from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Type

from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..core.model.base import Base
from ..model.typing_register_decorator import TypingDecorator
from .kv_store import KVStore
from .resource_data import ResourceData

if TYPE_CHECKING:
    from .resource_model import ResourceModel

# Typing names generated for the class Process
CONST_RESOURCE_TYPING_NAME = "RESOURCE.gws_core.Resource"


@TypingDecorator(unique_name="Resource", object_type="RESOURCE")
class Resource(Base):

    data: ResourceData

    # Provided at the Class level automatically by the @ResourceDecorator
    # //!\\ Do not modify theses values
    _typing_name: str = None
    _human_name: str = None
    _short_description: str = None

    def __init__(self, data: Dict = None):

        # check that the class level property _typing_name is set
        if self._typing_name == CONST_RESOURCE_TYPING_NAME and type(self) != Resource:  # pylint: disable=unidiomatic-typecheck
            raise BadRequestException(
                f"The resource {self.full_classname()} is not decorated with @ResourceDecorator, it can't be instantiate. Please decorate the process class with @ResourceDecorator")

        if data is None:
            self.data = ResourceData()
        else:
            self.data = ResourceData(data)

    def delete_resource(self) -> None:
        pass

    def export(self, file_path: str, file_format: str = None):
        """
        Export the resource to a repository

        :param file_path: The destination file path
        :type file_path: str
        """

        # @ToDo: ensure that this method is only called by an Exporter

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

    def data_is_kv_store(self) -> bool:
        return isinstance(self.data, KVStore)

    # -- T --

    def to_json(self) -> dict:
        return self.data.to_json()

    # TODO est-ce qu'on appel le clone automatiquement avant un process pour éviter de modifier une resource utilié ailleurs ?
    def clone(self) -> 'Resource':
        return Resource(self.data.clone())

    @classmethod
    def get_resource_model_type(cls) -> Type[ResourceModel]:
        """Return the resource model associated with this Resource
        //!\\ To overwrite only when you know what you are doing

        :return: [description]
        :rtype: Type[Any]
        """
        from .resource_model import ResourceModel
        return ResourceModel

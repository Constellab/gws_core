# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, Callable, Dict, List, Type

from gws_core.resource.view_types import ViewConfig

from ..core.classes.paginator import Paginator
from ..core.exception.exceptions import NotFoundException
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..core.service.base_service import BaseService
from ..experiment.experiment import Experiment
from ..model.typing_manager import TypingManager
from ..resource.view_decorator import ResourceViewMetaData
from ..resource.view_helper import ViewHelper
from .resource_model import Resource, ResourceModel
from .resource_typing import ResourceTyping


class ResourceService(BaseService):

    ############################# RESOURCE MODEL ###########################

    @classmethod
    def fetch_resource(cls,
                       resource_model_typing_name: str,
                       uri: str = "") -> ResourceModel:

        try:
            return TypingManager.get_object_with_typing_name_and_uri(resource_model_typing_name, uri)

        except Exception as err:
            raise NotFoundException(
                detail=f"No resource found with uri '{uri}' and type '{resource_model_typing_name}'") from err

    @classmethod
    def fetch_resource_list(cls,
                            resource_typing_name: str,
                            experiment_uri: str = None,
                            page: int = 0, number_of_items_per_page: int = 20) -> Paginator[ResourceModel]:

        # Retrieve the resource type
        resource_type: Type[Resource] = TypingManager.get_type_from_name(
            resource_typing_name)

        # Retrieve the resource model type from the resource type
        resource_model_type: Type[ResourceModel] = resource_type.get_resource_model_type()

        # request the resource model
        number_of_items_per_page = min(
            number_of_items_per_page, cls._number_of_items_per_page)

        if resource_model_type is ResourceModel:
            query = resource_model_type.select().order_by(resource_model_type.creation_datetime.desc())
        else:
            query = resource_model_type.select_me().order_by(resource_model_type.creation_datetime.desc())
        if experiment_uri:
            query = query.join(Experiment) \
                .where(Experiment.uri == experiment_uri)
        return Paginator(
            query, page=page, number_of_items_per_page=number_of_items_per_page)

    ############################# RESOURCE TYPE ###########################

    @classmethod
    def fetch_resource_type_list(cls,
                                 page: int = 0,
                                 number_of_items_per_page: int = 20) -> Paginator[ResourceTyping]:

        query = ResourceTyping.get_types()
        number_of_items_per_page = min(
            number_of_items_per_page, cls._number_of_items_per_page)
        return Paginator(
            query, page=page, number_of_items_per_page=number_of_items_per_page)

    ################################# VIEW ###############################

    @classmethod
    def get_views_of_resource(cls, resource_typing_name: str) -> List[ResourceViewMetaData]:
        resource_type: Type[Resource] = TypingManager.get_type_from_name(resource_typing_name)

        return cls.get_views_of_resource_type(resource_type)

    @classmethod
    def get_views_of_resource_type(cls, resource_type: Type[Resource]) -> List[ResourceViewMetaData]:
        if not issubclass(resource_type, Resource):
            raise BadRequestException("Can't find views of an object other than a Resource")
        return ViewHelper.get_views_of_resource_type(resource_type)

    @classmethod
    def call_view_on_resource_type(cls, resource_model_typing_name: str,
                                   resource_model_uri: str,
                                   view_name: str, config: ViewConfig) -> Any:

        resource_model: ResourceModel = cls.fetch_resource(resource_model_typing_name, resource_model_uri)

        resource: Resource = resource_model.get_resource()
        return cls.call_view_on_resource(resource, view_name, config)

    @classmethod
    def call_view_on_resource(cls, resource: Resource,
                              view_name: str, config: ViewConfig) -> Any:

        return ViewHelper.call_view_on_resource(resource, view_name, config)

# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Type, Union

from gws_core.model.typing_manager import TypingManager

from ..core.classes.paginator import Paginator
from ..core.exception.exceptions import NotFoundException
from ..core.service.base_service import BaseService
from ..experiment.experiment import Experiment
from .resource_model import CONST_RESOURCE_MODEL_TYPING_NAME, Resource
from .resource_type import ResourceType


class ResourceService(BaseService):

    # -- F --

    @classmethod
    def fetch_resource(cls,
                       typing_name: str = CONST_RESOURCE_MODEL_TYPING_NAME,
                       uri: str = "") -> Resource:

        try:
            return TypingManager.get_object_with_typing_name_and_uri(typing_name, uri)

        except Exception as err:
            raise NotFoundException(
                detail=f"No resource found with uri '{uri}' and type '{typing_name}'") from err

    @classmethod
    def fetch_resource_list(cls,
                            typing_name: str = CONST_RESOURCE_MODEL_TYPING_NAME,
                            experiment_uri: str = None,
                            page: int = 0, number_of_items_per_page: int = 20,
                            as_json=False) -> Union[Paginator, List[Resource], List[dict]]:

        model_type: Type[Resource] = TypingManager.get_type_from_name(
            typing_name)

        number_of_items_per_page = min(
            number_of_items_per_page, cls._number_of_items_per_page)

        if model_type is Resource:
            query = model_type.select().order_by(model_type.creation_datetime.desc())
        else:
            query = model_type.select_me().order_by(model_type.creation_datetime.desc())
        if experiment_uri:
            query = query.join(Experiment) \
                .where(Experiment.uri == experiment_uri)
        paginator = Paginator(
            query, page=page, number_of_items_per_page=number_of_items_per_page)
        if as_json:
            return paginator.to_json()
        else:
            return paginator

    @classmethod
    def fetch_resource_type_list(cls,
                                 page: int = 0,
                                 number_of_items_per_page: int = 20,
                                 as_json=False) -> Union[Paginator, dict]:

        query = ResourceType.get_types()
        number_of_items_per_page = min(
            number_of_items_per_page, cls._number_of_items_per_page)
        paginator = Paginator(
            query, page=page, number_of_items_per_page=number_of_items_per_page)
        if as_json:
            return paginator.to_json()
        else:
            return paginator

    @classmethod
    def fetch_resource_type_hierarchy(cls):
        pass

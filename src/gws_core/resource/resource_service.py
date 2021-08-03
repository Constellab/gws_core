# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Union

from ..core.classes.paginator import Paginator
from ..core.exception import NotFoundException
from ..core.model.model import Model
from ..core.model.typing import ResourceType
from ..core.service.base_service import BaseService
from ..experiment.experiment import Experiment
from ..resource.resource import Resource


class ResourceService(BaseService):

    # -- F --

    @classmethod
    def fetch_resource(cls,
                       type="gws.resource.Resource",
                       uri: str = "") -> Resource:
        t = None
        if type:
            t = Model.get_model_type(type)
            if t is None:
                raise NotFoundException(
                    detail=f"Resource type '{type}' not found")
        else:
            t = Resource

        try:
            r = t.get(t.uri == uri)
            return r
        except Exception as err:
            raise NotFoundException(
                detail=f"No resource found with uri '{uri}' and type '{type}'") from err

    @classmethod
    def fetch_resource_list(cls,
                            type="gws.resource.Resource",
                            search_text: str = "",
                            experiment_uri: str = None,
                            page: int = 1, number_of_items_per_page: int = 20,
                            as_json=False) -> Union[Paginator, List[Resource], List[dict]]:

        t = None
        if type:
            t = Model.get_model_type(type)
            if t is None:
                raise NotFoundException(
                    detail=f"Resource type '{type}' not found")
        else:
            t = Resource
        number_of_items_per_page = min(
            number_of_items_per_page, cls._number_of_items_per_page)
        if search_text:
            query = t.search(search_text)
            result = []
            for o in query:
                if as_json:
                    result.append(o.get_related().to_json(shallow=True))
                else:
                    result.append(o.get_related())
            paginator = Paginator(
                query, page=page, number_of_items_per_page=number_of_items_per_page)
            return {
                'data': result,
                'paginator': paginator.paginator_dict()
            }
        else:
            if t is Resource:
                query = t.select().order_by(t.creation_datetime.desc())
            else:
                query = t.select_me().order_by(t.creation_datetime.desc())
            if experiment_uri:
                query = query.join(Experiment) \
                    .where(Experiment.uri == experiment_uri)
            paginator = Paginator(
                query, page=page, number_of_items_per_page=number_of_items_per_page)
            if as_json:
                return paginator.to_json(shallow=True)
            else:
                return paginator

    @classmethod
    def fetch_resource_type_list(cls,
                                 page: int = 1,
                                 number_of_items_per_page: int = 20,
                                 as_json=False) -> (Paginator, dict):

        query = ResourceType.select().order_by(ResourceType.model_type.desc())
        number_of_items_per_page = min(
            number_of_items_per_page, cls._number_of_items_per_page)
        paginator = Paginator(
            query, page=page, number_of_items_per_page=number_of_items_per_page)
        if as_json:
            return paginator.to_json(shallow=True)
        else:
            return paginator

    @classmethod
    def fetch_resource_type_hierarchy(cls):
        pass

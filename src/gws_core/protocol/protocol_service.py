# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from ..core.service.base_service import BaseService
from ..core.exception.exceptions.not_found_exception import NotFoundException
from ..experiment.experiment import Experiment
from ..progress_bar.progress_bar import ProgressBar
from ..protocol.protocol import Protocol
from ..core.classes.paginator import Paginator
from ..core.model.typing import ProtocolType


class ProtocolService(BaseService):

    # -- F --

    @classmethod
    def fetch_protocol(cls, type="gws.protocol.Protocol", uri: str = "") -> Protocol:
        from .model_service import ModelService
        t = None
        if type:
            t = ModelService.get_model_type(type)
            if t is None:
                raise NotFoundException(
                    detail=f"Protocol type '{type}' not found")
        else:
            t = Protocol
        try:
            p = t.get(t.uri == uri)
            return p
        except Exception as err:
            raise NotFoundException(
                detail=f"No protocol found with uri '{uri}' and type '{type}'") from err

    @classmethod
    def fetch_protocol_progress_bar(cls, type="gws.protocol.Protocol", uri: str = "") -> ProgressBar:
        try:
            return ProgressBar.get((ProgressBar.process_uri == uri) & (ProgressBar.process_type == type))
        except Exception as err:
            raise NotFoundException(
                detail=f"No progress bar found with process_uri '{uri}' and process_type '{type}'") from err

    @classmethod
    def fetch_protocol_list(cls,
                            type="gws.protocol.Protocol",
                            search_text: str = "",
                            experiment_uri: str = None,
                            page: int = 1,
                            number_of_items_per_page: int = 20,
                            as_json=False) -> (Paginator, List[Protocol], List[dict], ):

        from .model_service import ModelService
        number_of_items_per_page = min(
            number_of_items_per_page, cls._number_of_items_per_page)
        t = None
        if type:
            t = ModelService.get_model_type(type)
            if t is None:
                raise NotFoundException(
                    detail=f"Protocol type '{type}' not found")
        else:
            t = Protocol

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
                'paginator': paginator._paginator_dict()
            }
        else:
            if t is Protocol:
                #query = t.select().where(t.is_protocol == True).order_by(t.creation_datetime.desc())
                query = t.select().where(t.is_template == False).order_by(t.creation_datetime.desc())
            else:
                #query = t.select().where(t.type == t.full_classname()).order_by(t.creation_datetime.desc())
                query = t.select().where((t.type == t.full_classname()) & (
                    t.is_template == False)).order_by(t.creation_datetime.desc())

            if experiment_uri:
                query = query.join(Experiment, on=(t.id == Experiment.protocol_id))\
                    .where(Experiment.uri == experiment_uri)

            paginator = Paginator(
                query, page=page, number_of_items_per_page=number_of_items_per_page)
            if as_json:
                return paginator.to_json(shallow=True)
            else:
                return paginator

    @classmethod
    def fetch_protocol_type_list(cls,
                                 page: int = 1,
                                 number_of_items_per_page: int = 20,
                                 as_json=False) -> (Paginator, dict):

        query = ProtocolType.select()\
                            .where(ProtocolType.root_model_type == "gws.protocol.Protocol")\
                            .order_by(ProtocolType.model_type.desc())

        number_of_items_per_page = min(
            number_of_items_per_page, cls._number_of_items_per_page)
        paginator = Paginator(
            query, page=page, number_of_items_per_page=number_of_items_per_page)
        if as_json:
            return paginator.to_json(shallow=True)
        else:
            return paginator

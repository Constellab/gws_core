# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Type, Union

from ..core.classes.paginator import Paginator
from ..core.exception.exceptions.not_found_exception import NotFoundException
from ..core.model.model import Model
from ..core.model.typing import ProtocolType
from ..core.service.base_service import BaseService
from ..experiment.experiment import Experiment
from ..progress_bar.progress_bar import ProgressBar
from ..protocol.protocol import Protocol


class ProtocolService(BaseService):

    # -- F --

    @classmethod
    def fetch_protocol(cls, type_str="gws_core.protocol.protocol.Protocol", uri: str = "") -> Protocol:
        model_type: Type[Model] = None
        if type_str:
            model_type = Model.get_model_type(type_str)
            if model_type is None:
                raise NotFoundException(
                    detail=f"Protocol type '{type_str}' not found")
        else:
            model_type = Protocol
        try:
            protocol = model_type.get(model_type.uri == uri)
            return protocol
        except Exception as err:
            raise NotFoundException(
                detail=f"No protocol found with uri '{uri}' and type '{type_str}'") from err

    @classmethod
    def fetch_protocol_progress_bar(cls, type="gws_core.protocol.protocol.Protocol", uri: str = "") -> ProgressBar:
        try:
            return ProgressBar.get((ProgressBar.process_uri == uri) & (ProgressBar.process_type == type))
        except Exception as err:
            raise NotFoundException(
                detail=f"No progress bar found with process_uri '{uri}' and process_type '{type}'") from err

    @classmethod
    def fetch_protocol_list(cls,
                            type_str="gws_core.protocol.protocol.Protocol",
                            search_text: str = "",
                            experiment_uri: str = None,
                            page: int = 1,
                            number_of_items_per_page: int = 20,
                            as_json=False) -> Union[Paginator, List[Protocol], List[dict]]:

        number_of_items_per_page = min(
            number_of_items_per_page, cls._number_of_items_per_page)
        model_type: Type[Model] = None
        if type_str:
            model_type = Model.get_model_type(type_str)
            if model_type is None:
                raise NotFoundException(
                    detail=f"Protocol type '{type_str}' not found")
        else:
            model_type = Protocol

        if search_text:
            query = model_type.search(search_text)
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
            if model_type is Protocol:
                #query = t.select().where(t.is_protocol == True).order_by(t.creation_datetime.desc())
                query = model_type.select().where(model_type.is_template is False).order_by(
                    model_type.creation_datetime.desc())
            else:
                #query = t.select().where(t.type == t.full_classname()).order_by(t.creation_datetime.desc())
                query = model_type.select().where((model_type.type == model_type.full_classname()) & (
                    model_type.is_template == False)).order_by(model_type.creation_datetime.desc())

            if experiment_uri:
                query = query.join(Experiment, on=(model_type.id == Experiment.protocol_id))\
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
                                 as_json=False) -> Union[Paginator, dict]:

        query = ProtocolType.select()\
                            .where(ProtocolType.root_model_type == "gws_core.protocol.protocol.Protocol")\
                            .order_by(ProtocolType.model_type.desc())

        number_of_items_per_page = min(
            number_of_items_per_page, cls._number_of_items_per_page)
        paginator = Paginator(
            query, page=page, number_of_items_per_page=number_of_items_per_page)
        if as_json:
            return paginator.to_json(shallow=True)
        else:
            return paginator

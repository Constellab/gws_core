# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Type, Union

from gws_core.core.dto.typed_tree_dto import TypedTree

from ..core.classes.paginator import Paginator
from ..core.exception.exceptions.not_found_exception import NotFoundException
from ..core.service.base_service import BaseService
from ..experiment.experiment import Experiment
from ..model.typing_manager import TypingManager
from ..protocol.protocol import CONST_PROTOCOL_TYPING_NAME, Protocol
from .protocol_type import ProtocolType


class ProtocolService(BaseService):

    # -- F --

    @classmethod
    def fetch_protocol(cls, typing_name=CONST_PROTOCOL_TYPING_NAME, uri: str = "") -> Protocol:
        return TypingManager.get_object_with_typing_name_and_uri(typing_name, uri)

    @classmethod
    def fetch_protocol_list(cls,
                            typing_name=CONST_PROTOCOL_TYPING_NAME,
                            experiment_uri: str = None,
                            page: int = 1,
                            number_of_items_per_page: int = 20,
                            as_json=False) -> Union[Paginator, List[Protocol], List[dict]]:

        number_of_items_per_page = min(
            number_of_items_per_page, cls._number_of_items_per_page)
        model_type: Type[Protocol] = None
        if typing_name:
            model_type = TypingManager.get_type_from_name(typing_name)
            if model_type is None:
                raise NotFoundException(
                    detail=f"Protocol type '{typing_name}' not found")
        else:
            model_type = Protocol

        if model_type is Protocol:
            query = model_type.select().where(model_type.is_template is False).order_by(
                model_type.creation_datetime.desc())
        else:
            query = model_type.select_me().where(model_type.is_template == False).order_by(
                model_type.creation_datetime.desc())

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
                            .where(ProtocolType.object_type == "PROTOCOL")\
                            .order_by(ProtocolType.model_type.desc())

        number_of_items_per_page = min(
            number_of_items_per_page, cls._number_of_items_per_page)
        paginator = Paginator(
            query, page=page, number_of_items_per_page=number_of_items_per_page)
        if as_json:
            return paginator.to_json(shallow=True)
        else:
            return paginator

    @classmethod
    def fetch_process_type_tree(cls) -> List[TypedTree]:
        """
        Return all the process types grouped by module and submodules
        """

        query: List[ProtocolType] = ProtocolType.select()\
            .where(ProtocolType.object_type == "PROTOCOL")\
            .order_by(ProtocolType.model_type.asc())

        # create a fake main group to add processes in it
        tree: TypedTree = TypedTree('')

        for process_type in query:
            tree.add_object(
                process_type.get_model_types_array(), process_type.to_json())

        return tree.sub_trees

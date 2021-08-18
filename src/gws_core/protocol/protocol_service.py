# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Type, Union

from gws_core.core.dto.typed_tree_dto import TypedTree
from peewee import ModelSelect

from ..core.classes.paginator import Paginator
from ..core.service.base_service import BaseService
from ..process.process_model import ProcessModel
from ..process.processable_factory import ProcessableFactory
from ..protocol.protocol_model import ProtocolModel
from .protocol import Protocol
from .protocol_type import ProtocolType


class ProtocolService(BaseService):

    # -- F --

    @classmethod
    def get_protocol_by_uri(cls, uri: str) -> ProtocolModel:
        return ProtocolModel.get_by_uri(uri)

    @classmethod
    def fetch_protocol_list(cls,
                            page: int = 1,
                            number_of_items_per_page: int = 20,
                            as_json=False) -> Union[Paginator, List[ProtocolModel], List[dict]]:

        number_of_items_per_page = min(
            number_of_items_per_page, cls._number_of_items_per_page)
        model_type: Type[ProtocolModel] = None

        query: ModelSelect = ProtocolModel.select().order_by(
            model_type.creation_datetime.desc())

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

        query = ProtocolType.get_types()

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

        query: List[ProtocolType] = ProtocolType.get_types()

        # create a fake main group to add processes in it
        tree: TypedTree = TypedTree('')

        for process_type in query:
            tree.add_object(
                process_type.get_model_types_array(), process_type.to_json())

        return tree.sub_trees

    @classmethod
    def create_process_from_type(cls, protocol_type: Type[Protocol], instance_name: str = None) -> ProcessModel:
        protocol: ProtocolModel = ProcessableFactory.create_protocol_from_type(
            protocol_type=protocol_type, instance_name=instance_name)

        protocol.save_full()
        return protocol

    @classmethod
    def create_protocol_from_data(cls, processes: dict = None,
                                  connectors: list = None,
                                  interfaces: dict = None,
                                  outerfaces: dict = None,
                                  instance_name: str = None) -> ProcessModel:
        protocol: ProtocolModel = ProcessableFactory.create_protocol_from_data(
            processes=processes,
            connectors=connectors,
            interfaces=interfaces,
            outerfaces=outerfaces,
            instance_name=instance_name)

        protocol.save_full()
        return protocol

    @classmethod
    def create_protocol_from_graph(cls, graph: dict) -> ProcessModel:
        protocol: ProtocolModel = ProcessableFactory.create_protocol_from_graph(
            graph=graph)

        protocol.save_full()
        return protocol

    @classmethod
    def create_protocol_from_process(cls, process: ProcessModel) -> ProcessModel:
        protocol: ProtocolModel = ProtocolService.create_protocol_from_data(
            processes={process.instance_name: process}, connectors=[], interfaces={}, outerfaces={})

        protocol.save_full()
        return protocol

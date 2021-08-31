# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Type, Union

from peewee import ModelSelect

from ..core.classes.paginator import Paginator
from ..core.dto.typed_tree_dto import TypedTree
from ..core.service.base_service import BaseService
from ..process.process_model import ProcessModel
from ..processable.processable_factory import ProcessableFactory
from ..processable.sub_processable_factory import SubProcessFactoryUpdate
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
                            page: int = 0,
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
            return paginator.to_json()
        else:
            return paginator

    @classmethod
    def create_protocol_from_type(cls, protocol_type: Type[Protocol], instance_name: str = None) -> ProtocolModel:
        protocol: ProtocolModel = ProcessableFactory.create_protocol_model_from_type(
            protocol_type=protocol_type, instance_name=instance_name)

        protocol.save_full()
        return protocol

    @classmethod
    def create_protocol_from_data(cls, processes: dict = None,
                                  connectors: list = None,
                                  interfaces: dict = None,
                                  outerfaces: dict = None,
                                  instance_name: str = None) -> ProtocolModel:
        protocol: ProtocolModel = ProcessableFactory.create_protocol_model_from_data(
            processes=processes,
            connectors=connectors,
            interfaces=interfaces,
            outerfaces=outerfaces,
            instance_name=instance_name)

        protocol.save_full()
        return protocol

    @classmethod
    def create_protocol_from_graph(cls, graph: dict) -> ProtocolModel:
        protocol: ProtocolModel = ProcessableFactory.create_protocol_model_from_graph(
            graph=graph)

        protocol.save_full()
        return protocol

    @classmethod
    def create_protocol_from_process(cls, process: ProcessModel) -> ProtocolModel:
        protocol: ProtocolModel = ProtocolService.create_protocol_from_data(
            processes={process.instance_name: process}, connectors=[], interfaces={}, outerfaces={})

        protocol.save_full()
        return protocol

    @classmethod
    def update_protocol_graph(cls, protocol: ProtocolModel, graph: dict) -> ProtocolModel:
        new_protocol: ProtocolModel = cls._update_protocol_graph_recur(
            protocol, graph)

        new_protocol.save_full()
        return new_protocol

    @classmethod
    def _update_protocol_graph_recur(cls, protocol: ProtocolModel, graph: dict) -> ProtocolModel:

        for process in protocol.processes.values():
            # disconnect the port to prevent connection errors later
            process.disconnect()

        cls.remove_orphan_process(protocol=protocol, nodes=graph["nodes"])

        protocol.build_from_graph(
            graph=graph, sub_processable_factory=SubProcessFactoryUpdate())

        for key, processable in protocol.processes.items():

            # If this is a sub protocol and it's graph is defined
            if isinstance(processable, ProtocolModel) and 'graph' in graph["nodes"][key]['data']:
                cls._update_protocol_graph_recur(
                    protocol=processable, graph=graph["nodes"][key]["data"]["graph"])

        # Init the connector afterward because its needs the child to init correctly
        protocol.init_connectors_from_graph(graph["links"])

        return protocol

    @classmethod
    def remove_orphan_process(cls, protocol: ProtocolModel, nodes: dict) -> None:
        """Method to remove the removed process when saving a new protocols

        :param nodes: [description]
        :type nodes: Dict
        """
        deleted_keys = []
        for key, process in protocol.processes.items():
            # if the process is not in the Dict or its type has changed, remove it
            if not key in nodes or process.processable_typing_name != nodes[key].get("processable_typing_name"):
                deleted_keys.append(key)

        for key in deleted_keys:
            protocol.delete_process(key)

    ############################# PROTOCOL TYPE ###########################

    @classmethod
    def get_protocol_type(cls, uri: str) -> ProtocolType:
        return ProtocolType.get_by_uri_and_check(uri)

    @classmethod
    def fetch_protocol_type_list(cls,
                                 page: int = 0,
                                 number_of_items_per_page: int = 20) -> Paginator[ProtocolType]:

        query = ProtocolType.get_types()

        number_of_items_per_page = min(
            number_of_items_per_page, cls._number_of_items_per_page)
        return Paginator(
            query, page=page, number_of_items_per_page=number_of_items_per_page)

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

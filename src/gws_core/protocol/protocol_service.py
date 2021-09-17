# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Tuple, Type

from gws_core.io.connector import Connector
from gws_core.io.port import InPort, OutPort
from gws_core.process.process import Process
from peewee import ModelSelect

from ..config.config_types import ConfigParamsDict
from ..core.classes.paginator import Paginator
from ..core.decorator.transaction import transaction
from ..core.dto.typed_tree_dto import TypedTree
from ..core.exception.exceptions import BadRequestException
from ..core.service.base_service import BaseService
from ..model.typing import Typing
from ..model.typing_manager import TypingManager
from ..process.process_factory import ProcessFactory
from ..process.process_model import ProcessModel
from ..process.protocol_sub_process_builder import SubProcessBuilderUpdate
from ..protocol.protocol_model import ProtocolModel
from ..task.task_model import TaskModel
from .protocol import Protocol
from .protocol_typing import ProtocolTyping


class ProtocolService(BaseService):

    ########################## GET #####################

    @classmethod
    def get_protocol_by_uri(cls, uri: str) -> ProtocolModel:
        return ProtocolModel.get_by_uri_and_check(uri)

    @classmethod
    def fetch_protocol_list(cls,
                            page: int = 0,
                            number_of_items_per_page: int = 20) -> Paginator[ProtocolModel]:

        number_of_items_per_page = min(
            number_of_items_per_page, cls._number_of_items_per_page)
        model_type: Type[ProtocolModel] = None

        query: ModelSelect = ProtocolModel.select().order_by(
            model_type.creation_datetime.desc())

        return Paginator(
            query, page=page, number_of_items_per_page=number_of_items_per_page)

    ########################## CREATE #####################
    @classmethod
    def create_protocol_model_from_type(cls, protocol_type: Type[Protocol], instance_name: str = None,
                                        config_params: ConfigParamsDict = None) -> ProtocolModel:
        protocol: ProtocolModel = ProcessFactory.create_protocol_model_from_type(
            protocol_type=protocol_type, instance_name=instance_name, config_params=config_params)

        protocol.save_full()
        return protocol

    @classmethod
    def create_protocol_model_from_data(cls, processes: dict = None,
                                        connectors: list = None,
                                        interfaces: dict = None,
                                        outerfaces: dict = None,
                                        instance_name: str = None) -> ProtocolModel:
        protocol: ProtocolModel = ProcessFactory.create_protocol_model_from_data(
            processes=processes,
            connectors=connectors,
            interfaces=interfaces,
            outerfaces=outerfaces,
            instance_name=instance_name)

        protocol.save_full()
        return protocol

    @classmethod
    def create_empty_protocol(cls, instance_name: str = None) -> ProtocolModel:
        protocol: ProtocolModel = ProcessFactory.create_protocol_empty(instance_name=instance_name)

        protocol.save_full()
        return protocol

    @classmethod
    def create_protocol_model_from_graph(cls, graph: dict) -> ProtocolModel:
        protocol: ProtocolModel = ProcessFactory.create_protocol_model_from_graph(
            graph=graph)

        protocol.save_full()
        return protocol

    @classmethod
    def create_protocol_model_from_task_model(cls, task_model: TaskModel) -> ProtocolModel:
        if not isinstance(task_model, TaskModel):
            raise BadRequestException("A PocessModel is required")
        protocol: ProtocolModel = ProtocolService.create_protocol_model_from_data(
            processes={task_model.instance_name: task_model}, connectors=[], interfaces={}, outerfaces={})

        protocol.save_full()
        return protocol

    ########################## UPDATE PROCESS #####################
    @classmethod
    def update_protocol_graph(cls, protocol_model: ProtocolModel, graph: dict) -> ProtocolModel:
        new_protocol: ProtocolModel = cls._update_protocol_graph_recur(
            protocol_model, graph)

        new_protocol.save_full()
        return new_protocol

    @classmethod
    def _update_protocol_graph_recur(cls, protocol_model: ProtocolModel, graph: dict) -> ProtocolModel:

        for process in protocol_model.processes.values():
            # disconnect the port to prevent connection errors later
            process.disconnect()

        cls.remove_orphan_process(protocol_model=protocol_model, nodes=graph["nodes"])

        protocol_model.build_from_graph(
            graph=graph, sub_process_factory=SubProcessBuilderUpdate())

        for key, process in protocol_model.processes.items():

            # If this is a sub protocol and it's graph is defined
            if isinstance(process, ProtocolModel) and 'graph' in graph["nodes"][key]['data']:
                cls._update_protocol_graph_recur(
                    protocol_model=process, graph=graph["nodes"][key]["data"]["graph"])

        # Init the connector afterward because its needs the child to init correctly
        protocol_model.init_connectors_from_graph(graph["links"])

        return protocol_model

    @classmethod
    def remove_orphan_process(cls, protocol_model: ProtocolModel, nodes: dict) -> None:
        """Method to remove the removed process when saving a new protocols

        :param nodes: [description]
        :type nodes: Dict
        """
        deleted_keys = []
        for key, process in protocol_model.processes.items():
            # if the process is not in the Dict or its type has changed, remove it
            if not key in nodes or process.process_typing_name != nodes[key].get("process_typing_name"):
                deleted_keys.append(key)

        for key in deleted_keys:
            protocol_model.remove_process(key)

    @classmethod
    @transaction()
    def add_process_to_protocol_uri(cls, protocol_uri: str, process_typing_name: str) -> ProcessModel:
        protocol_model: ProtocolModel = ProtocolModel.get_by_uri_and_check(protocol_uri)

        process_typing: Typing = TypingManager.get_typing_from_name(process_typing_name)

        # get the instance name from type model name
        instance_name = protocol_model.generate_unique_instance_name(process_typing.model_name)

        return cls.add_process_to_protocol(protocol_model=protocol_model, process_type=process_typing.get_type(),
                                           instance_name=instance_name)

    @classmethod
    @transaction()
    def add_empty_protocol_to_protocol(cls, protocol_model: ProtocolModel, instance_name: str) -> ProcessModel:
        child_protocol_model: ProtocolModel = ProcessFactory.create_protocol_empty()

        return cls.add_process_model_to_protocol(protocol_model=protocol_model, process_model=child_protocol_model,
                                                 instance_name=instance_name)

    @classmethod
    @transaction()
    def add_process_to_protocol(cls, protocol_model: ProtocolModel, process_type: Type[Process],
                                instance_name: str, config_params: ConfigParamsDict = None) -> ProcessModel:
        # create the process
        process_model: ProcessModel = ProcessFactory.create_process_model_from_type(
            process_type=process_type, config_params=config_params, instance_name=instance_name)

        return cls.add_process_model_to_protocol(protocol_model=protocol_model, process_model=process_model,
                                                 instance_name=instance_name)

    @classmethod
    @transaction()
    def add_process_model_to_protocol(cls, protocol_model: ProtocolModel, process_model: ProcessModel,
                                      instance_name: str) -> ProcessModel:
        protocol_model.add_process_model(instance_name=instance_name, process_model=process_model)
        # save the new process
        process_model.save_full()

        # Refresh the protocol graph and save
        protocol_model.save(update_graph=True)

        return process_model

    @classmethod
    @transaction()
    def delete_process_of_protocol(cls, protocol_model: ProtocolModel, process_instance_name: str) -> None:

        process_model: ProcessModel = protocol_model.get_process(process_instance_name)

        # delete the process form the DB
        process_model.delete_instance()

        # delete the process from the parent protocol
        protocol_model.remove_process(process_instance_name)
        protocol_model.save(update_graph=True)

    ########################## CONNECTORS #####################

    @classmethod
    def add_connectors_to_protocol(
            cls, protocol_model: ProtocolModel, connectors: List[Tuple[OutPort, InPort]]) -> ProtocolModel:
        for connector in connectors:
            new_connector: Connector = Connector(connector[0], connector[1])
            protocol_model.add_connector(new_connector)
        return protocol_model.save(update_graph=True)

    @classmethod
    def add_connector_to_protocol(
            cls, protocol_model: ProtocolModel, out_port: OutPort, in_port: InPort) -> ProtocolModel:
        connector: Connector = Connector(out_port, in_port)
        protocol_model.add_connector(connector)
        return protocol_model.save(update_graph=True)

    ########################## INTERFACE & OUTERFACE #####################
    @classmethod
    def add_interface_to_protocol(
            cls, protocol_model: ProtocolModel, name: str, in_port: InPort) -> ProtocolModel:
        protocol_model.add_interface(name, in_port)
        return protocol_model.save(update_graph=True)

    @classmethod
    def add_outerface_to_protocol(
            cls, protocol_model: ProtocolModel, name: str, out_port: OutPort) -> ProtocolModel:
        protocol_model.add_outerface(name, out_port)
        return protocol_model.save(update_graph=True)

    @classmethod
    def delete_interface_on_protocol(cls, protocol_model: ProtocolModel, interface_name: str) -> None:
        protocol_model.remove_interface(interface_name)
        protocol_model.save(update_graph=True)

    @classmethod
    def delete_outerface_on_protocol(cls, protocol_model: ProtocolModel, outerface_name: str) -> None:
        protocol_model.remove_outerface(outerface_name)
        protocol_model.save(update_graph=True)

    ############################# PROTOCOL TYPE ###########################

    @classmethod
    def get_protocol_type(cls, uri: str) -> ProtocolTyping:
        return ProtocolTyping.get_by_uri_and_check(uri)

    @classmethod
    def fetch_protocol_type_list(cls,
                                 page: int = 0,
                                 number_of_items_per_page: int = 20) -> Paginator[ProtocolTyping]:

        query = ProtocolTyping.get_types()

        number_of_items_per_page = min(
            number_of_items_per_page, cls._number_of_items_per_page)
        return Paginator(
            query, page=page, number_of_items_per_page=number_of_items_per_page)

    @classmethod
    def fetch_protocol_type_tree(cls) -> List[TypedTree]:
        """
        Return all the protocol types grouped by module and submodules
        """

        query: List[ProtocolTyping] = ProtocolTyping.get_types()

        # create a fake main group to add protocols in it
        tree: TypedTree = TypedTree('')

        for protocol_type in query:
            tree.add_object(
                protocol_type.get_model_types_array(), protocol_type.to_json())

        return tree.sub_trees

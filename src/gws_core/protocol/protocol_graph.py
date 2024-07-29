

from typing import Dict, List, Optional, Set

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.protocol.protocol_dto import (ProcessConfigDTO,
                                            ProtocolGraphConfigDTO)
from gws_core.task.plug import Sink, Source


class ResourceTaskOrigin(BaseModelDTO):
    task_origin_instance_path: str
    port_name: str


class ProtocolGraph():

    graph: ProtocolGraphConfigDTO

    def __init__(self, graph: ProtocolGraphConfigDTO) -> None:
        self.graph = graph

    def get_input_resource_ids(self) -> Set[str]:
        resource_ids: Set[str] = set()

        for node in self.graph.nodes.values():
            if node.process_typing_name == Source.get_typing_name():
                resource_id = Source.get_resource_id_from_config(node.config.values)
                if resource_id:
                    resource_ids.add(resource_id)

        return resource_ids

    def get_output_resource_ids(self) -> Set[str]:
        resource_ids: Set[str] = set()

        for node in self.graph.nodes.values():
            if node.process_typing_name == Sink.get_typing_name():
                resource_id = node.inputs.ports[Sink.input_name].resource_id
                if resource_id:
                    resource_ids.add(resource_id)

        return resource_ids

    def get_input_and_output_resource_ids(self) -> Set[str]:
        return self.get_input_resource_ids().union(self.get_output_resource_ids())

    def get_all_resource_ids(self) -> Set[str]:
        all_resource_ids = self._get_all_resource_ids_recursive(set(), self.graph)

        # we add the input ids to the set of all resource ids
        return all_resource_ids.union(self.get_input_resource_ids())

    def _get_all_resource_ids_recursive(self, resource_ids: Set[str], graph: ProtocolGraphConfigDTO) -> Set[str]:

        for node in graph.nodes.values():
            for port in node.outputs.ports.values():
                if port.resource_id:
                    resource_ids.add(port.resource_id)

            if node.graph:
                self._get_all_resource_ids_recursive(resource_ids, node.graph)

        return resource_ids

    def get_process_by_instance_path(self, instance_path: str) -> Optional[ProcessConfigDTO]:
        return self._get_process_by_instance_path_recursive(instance_path, self.graph)

    def _get_process_by_instance_path_recursive(
            self, instance_path: str, graph: ProtocolGraphConfigDTO) -> Optional[ProcessConfigDTO]:

        instance_names = instance_path.split('.')

        process = graph.nodes[instance_names[0]]

        if len(instance_names) == 1:
            return process

        # if we need to get a sub process
        if process.graph is None:
            raise Exception(f"Process '{process.instance_name}' is not a protocol")

        return self._get_process_by_instance_path_recursive('.'.join(instance_names[1:]), process.graph)

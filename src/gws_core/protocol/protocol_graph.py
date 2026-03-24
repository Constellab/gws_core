from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.process.process_types import ProcessStatus
from gws_core.protocol.protocol_dto import ProcessConfigDTO, ProtocolGraphConfigDTO
from gws_core.task.plug.input_task import InputTask
from gws_core.task.plug.output_task import OutputTask


class ResourceTaskOrigin(BaseModelDTO):
    task_origin_instance_path: str
    port_name: str


class ProtocolGraph:
    graph: ProtocolGraphConfigDTO

    def __init__(self, graph: ProtocolGraphConfigDTO) -> None:
        self.graph = graph

    def get_input_resource_ids(self) -> set[str]:
        resource_ids: set[str] = set()

        for node in self.graph.nodes.values():
            if node.process_typing_name == InputTask.get_typing_name():
                resource_id = InputTask.get_resource_id_from_config(node.config.values)
                if resource_id:
                    resource_ids.add(resource_id)

        return resource_ids

    def get_output_resource_ids(self) -> set[str]:
        resource_ids: set[str] = set()

        for node in self.graph.nodes.values():
            if node.process_typing_name == OutputTask.get_typing_name():
                resource_id = node.inputs.ports[OutputTask.input_name].resource_id
                if resource_id:
                    resource_ids.add(resource_id)

        return resource_ids

    def get_input_and_output_resource_ids(self) -> set[str]:
        return self.get_input_resource_ids().union(self.get_output_resource_ids())

    def get_all_resource_ids(self) -> set[str]:
        all_resource_ids = self._get_all_resource_ids_recursive(set(), self.graph)

        # we add the input ids to the set of all resource ids
        return all_resource_ids.union(self.get_input_resource_ids())

    def _get_all_resource_ids_recursive(
        self, resource_ids: set[str], graph: ProtocolGraphConfigDTO
    ) -> set[str]:
        for node in graph.nodes.values():
            for port in node.outputs.ports.values():
                if port.resource_id:
                    resource_ids.add(port.resource_id)

            if node.graph:
                self._get_all_resource_ids_recursive(resource_ids, node.graph)

        return resource_ids

    def get_input_resource_ids_of_draft_tasks(self) -> set[str]:
        """Get input resource IDs of tasks that are in DRAFT status.

        For each task node in DRAFT status, collect the resource IDs from its input ports.
        This is useful for partially run scenarios where only the draft tasks need their inputs downloaded.
        """
        resource_ids: set[str] = set()
        self._collect_input_resource_ids_of_draft_tasks(resource_ids, self.graph)
        return resource_ids

    def _collect_input_resource_ids_of_draft_tasks(
        self, resource_ids: set[str], graph: ProtocolGraphConfigDTO
    ) -> None:
        for node in graph.nodes.values():
            # Skip InputTask and OutputTask nodes
            if node.process_typing_name in (
                InputTask.get_typing_name(),
                OutputTask.get_typing_name(),
            ):
                continue

            if node.status == ProcessStatus.DRAFT.value:
                # Collect resource IDs from input ports of this draft task
                for port in node.inputs.ports.values():
                    if port.resource_id:
                        resource_ids.add(port.resource_id)

            # Recurse into sub-protocols
            if node.graph:
                self._collect_input_resource_ids_of_draft_tasks(resource_ids, node.graph)

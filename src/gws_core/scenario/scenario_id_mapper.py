from gws_core.process.process_model import ProcessModel
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.resource.id_mapper import IdMapper
from gws_core.resource.resource_model import ResourceModel
from gws_core.scenario.scenario import Scenario
from gws_core.task.plug.input_task import InputTask


class ScenarioIdMapper(IdMapper):
    """Generates new IDs and replaces all cross-references in-memory.

    Used during scenario import in NEW_ID mode to replace all original IDs
    with fresh UUIDs while maintaining referential integrity across
    scenario, processes, resource models, ports, and configs.
    """

    def apply_new_ids(
        self,
        protocol_model: ProtocolModel,
        scenario: Scenario,
    ) -> None:
        """Replace all IDs with fresh UUIDs and update all cross-references.

        This is the single public entry point that orchestrates all ID replacements.
        """
        self._apply_to_scenario(scenario)
        self._apply_to_protocol(protocol_model)
        protocol_model.scenario = scenario  # Ensure protocol references the updated scenario
        self._apply_to_resource_models(protocol_model)

    def _apply_to_scenario(self, scenario: Scenario) -> None:
        """Replace the scenario ID with a new UUID."""
        scenario.id = self.generate_new_id(scenario.id)

    def _apply_to_protocol(self, protocol: ProtocolModel) -> None:
        """Recursively replace IDs in protocol and all sub-processes."""
        protocol.id = self.generate_new_id(protocol.id)
        self._update_progress_bar(protocol)
        for process in protocol.processes.values():
            if isinstance(process, ProtocolModel):
                self._apply_to_protocol(process)
            else:
                process.id = self.generate_new_id(process.id)
                self._update_progress_bar(process)

    def _update_progress_bar(self, process: ProcessModel) -> None:
        """Update the progress bar's process_id to match the new process ID."""
        if process.progress_bar is not None:
            process.progress_bar.process_id = process.id

    def _apply_to_resource_models(
        self,
        protocol_model: ProtocolModel,
    ) -> None:
        """Replace resource model IDs, parent_resource_id, scenario, and task_model references."""

        processes = protocol_model.get_all_processes_flatten_sort_by_start_date()

        for process in processes:
            # For TaskInput task set the resource ID in the config
            if process.is_input_task():
                old_resource_id = process.config.get_value(InputTask.config_name)
                process.set_config_value(
                    InputTask.config_name, self.generate_new_id(old_resource_id)
                )

            for port in process.inputs.ports.values():
                new_id = self.generate_new_id(port.get_resource_model_id())
                port.set_resource_model_id(new_id)
            for port in process.outputs.ports.values():
                new_id = self.generate_new_id(port.get_resource_model_id())
                port.set_resource_model_id(new_id)

    def _apply_to_ports(
        self, protocol: ProtocolModel, resource_models_by_id: dict[str, ResourceModel]
    ) -> None:
        """Replace resource models in all ports recursively."""
        for process in protocol.processes.values():
            for port in process.inputs.ports.values():
                new_id = self.get_new_id(port.get_resource_model_id())
                port.set_resource_model(resource_models_by_id.get(new_id) if new_id else None)
            for port in process.outputs.ports.values():
                new_id = self.get_new_id(port.get_resource_model_id())
                port.set_resource_model(resource_models_by_id.get(new_id) if new_id else None)
            if isinstance(process, ProtocolModel):
                self._apply_to_ports(process, resource_models_by_id)

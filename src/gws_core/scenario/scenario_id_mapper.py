from gws_core.process.process_model import ProcessModel
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.resource.id_mapper import IdMapper
from gws_core.resource.resource_model import ResourceModel
from gws_core.scenario.scenario import Scenario
from gws_core.task.plug.input_task import InputTask
from gws_core.task.task_model import TaskModel


class ScenarioIdMapper(IdMapper):
    """Generates new IDs and replaces all cross-references in-memory.

    Used during scenario import in NEW_ID mode to replace all original IDs
    with fresh UUIDs while maintaining referential integrity across
    scenario, processes, resource models, ports, and configs.
    """

    def apply_new_ids(
        self,
        protocol_model: ProtocolModel,
        resource_models: list[ResourceModel],
        scenario: Scenario,
    ) -> None:
        """Replace all IDs with fresh UUIDs and update all cross-references.

        This is the single public entry point that orchestrates all ID replacements.
        """
        old_scenario_id = scenario.id
        self._apply_to_scenario(scenario)
        self._apply_to_protocol(protocol_model)
        protocol_model.scenario = scenario  # Ensure protocol references the updated scenario
        self._apply_to_resource_models(resource_models, scenario, protocol_model, old_scenario_id)
        resource_models_by_id = {model.id: model for model in resource_models}
        self._apply_to_ports(protocol_model, resource_models_by_id)
        self._apply_to_input_task_configs(protocol_model)

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
        resource_models: list[ResourceModel],
        scenario: Scenario,
        protocol_model: ProtocolModel,
        old_scenario_id: str | None = None,
    ) -> None:
        """Replace resource model IDs, parent_resource_id, scenario, and task_model references."""
        for resource_model in resource_models:
            resource_model.id = self.generate_new_id(resource_model.id)
            resource_model.parent_resource_id = self.get_new_id(resource_model.parent_resource_id)

            # update the resource scenario if the scenario that generated the resource is the current scenario.
            # We use old_scenario_id for comparison because scenario.id has already been mutated to the new UUID.
            # Re-assigning the scenario object forces Peewee to flush its internal FK ID cache so the new
            # scenario ID is persisted on save. We also check identity (is) to handle the case where
            # resource_model.scenario is the same Python object as scenario (already mutated ID).
            if (
                resource_model.scenario is not None
                and old_scenario_id is not None
                and (
                    resource_model.scenario is scenario
                    or resource_model.scenario.id == old_scenario_id
                )
            ):
                resource_model.scenario = scenario

            # update the resource task_model if the task_model that generated the resource is in the protocol
            if resource_model.task_model is not None:
                new_task_id = self.get_new_id(resource_model.task_model.id)
                if new_task_id:
                    process = protocol_model.get_process_by_id(new_task_id)
                    if not process or not isinstance(process, TaskModel):
                        raise Exception(
                            f"Task model with id {new_task_id} not found for resource model {resource_model.id}"
                        )
                    resource_model.task_model = process

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

    def _apply_to_input_task_configs(self, protocol: ProtocolModel) -> None:
        """Replace resource_id in InputTask config values."""
        for process in protocol.processes.values():
            if process.is_input_task():
                old_resource_id = process.config.get_value(InputTask.config_name)
                process.set_config_value(InputTask.config_name, self.get_new_id(old_resource_id))
            if isinstance(process, ProtocolModel):
                self._apply_to_input_task_configs(process)

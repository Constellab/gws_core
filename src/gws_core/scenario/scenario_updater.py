from uuid import uuid4

from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.db.gws_core_db_manager import GwsCoreDbManager
from gws_core.entity_navigator.entity_navigator_service import EntityNavigatorService
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.protocol.protocol_service import ProtocolService
from gws_core.scenario.scenario import Scenario
from gws_core.scenario.scenario_loader import ScenarioLoader
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.tag import Tag
from gws_core.tag.tag_entity_type import TagEntityType


class ScenarioUpdater:
    """Updates an existing scenario by diffing its protocol graph against a new version.

    Mirrors the ScenarioLoader pattern: accepts inputs via constructor, then
    exposes an ``update_scenario()`` entry-point that orchestrates metadata
    update, recursive protocol diff, and tag replacement.
    """

    _existing_scenario: Scenario
    _scenario_loader: ScenarioLoader
    _message_dispatcher: MessageDispatcher
    _origin_lab_id: str | None

    def __init__(
        self,
        existing_scenario: Scenario,
        scenario_loader: ScenarioLoader,
        message_dispatcher: MessageDispatcher | None = None,
        origin_lab_id: str | None = None,
    ) -> None:
        self._existing_scenario = existing_scenario
        self._scenario_loader = scenario_loader
        self._message_dispatcher = message_dispatcher or MessageDispatcher()
        self._origin_lab_id = origin_lab_id

    @GwsCoreDbManager.transaction()
    def update_scenario(self, skip_tags: bool = False) -> Scenario:
        """Update the existing scenario in place from the loaded scenario data.

        1. Validates the scenario can be updated
        2. Updates scenario metadata (title, description, status, folder, error_info)
        3. Diffs the protocol graph (add/update/remove processes)
        4. Replaces tags if requested

        Returns the updated existing scenario.
        """
        scenario = self._existing_scenario

        # Validate
        scenario.check_is_updatable()
        if scenario.is_running:
            raise Exception("Cannot update a running scenario")

        # Update metadata
        new_scenario = self._scenario_loader.get_scenario()
        self._update_scenario_metadata(scenario, new_scenario)

        # Diff protocol graph
        new_protocol = self._scenario_loader.get_protocol_model()
        existing_protocol = scenario.protocol_model
        self._diff_protocol(existing_protocol, new_protocol)

        # Update tags
        if not skip_tags:
            self._update_tags(scenario.id, self._scenario_loader.get_tags())
        else:
            self._message_dispatcher.notify_info_message("Skipping scenario tags")

        return scenario

    def get_existing_scenario(self) -> Scenario:
        """Return the existing scenario being updated."""
        return self._existing_scenario

    def get_existing_protocol(self) -> ProtocolModel:
        """Return the existing protocol model after update."""
        return self._existing_scenario.protocol_model

    # ──────────────────────────── private helpers ────────────────────────────

    def _update_scenario_metadata(self, existing: Scenario, new_scenario: Scenario) -> None:
        """Overwrite scenario-level fields from the new version."""
        self._message_dispatcher.notify_info_message("Updating scenario metadata")
        existing.copy_from_and_save(new_scenario)

    def _diff_protocol(self, existing_protocol: ProtocolModel, new_protocol: ProtocolModel) -> None:
        """Recursively diff old and new protocol graphs, updating/adding/removing processes."""
        self._message_dispatcher.notify_info_message("Diffing protocol graph")

        old_processes = dict(existing_protocol.processes)
        new_processes = dict(new_protocol.processes)

        # REMOVE: processes in old but not in new
        for process_instance_name, old_process in old_processes.items():
            if process_instance_name not in new_processes:
                self._message_dispatcher.notify_info_message(
                    f"Removing process '{old_process.instance_name}'"
                )
                EntityNavigatorService.reset_process_of_protocol_id(
                    existing_protocol.id, process_instance_name
                )
                ProtocolService.delete_process_of_protocol_id(
                    existing_protocol.id, process_instance_name
                )

        # UPDATE: processes that exist in both
        for process_instance_name, new_process in new_processes.items():
            if process_instance_name in old_processes:
                old_process = old_processes[process_instance_name]

                if isinstance(old_process, ProtocolModel) and isinstance(
                    new_process, ProtocolModel
                ):
                    old_process.copy_from_and_save(new_process)
                    self._diff_protocol(old_process, new_process)
                else:
                    old_process.copy_from_and_save(new_process)

        # ADD: processes in new but not in old
        for process_instance_name, new_process in new_processes.items():
            if process_instance_name not in old_processes:
                self._message_dispatcher.notify_info_message(
                    f"Adding new process '{new_process.instance_name}'"
                )
                # TODO to fix
                # Generate a fresh ID to avoid conflicts with existing DB records
                new_process.id = str(uuid4())
                new_process.set_parent_protocol(existing_protocol)
                new_process.set_scenario(existing_protocol.scenario)
                new_process.save_full()
                existing_protocol.add_process_model(
                    new_process, instance_name=process_instance_name
                )

        # TODO this is not great
        # Reload processes from DB after removals
        existing_protocol.reload_graph()

        # Update protocol graph structure (connectors, interfaces, outerfaces, layout)
        existing_protocol.copy_graph_from_and_save(new_protocol)

    def _update_tags(self, scenario_id: str, tags: list[Tag]) -> None:
        """Delete existing tags and add new ones."""
        self._message_dispatcher.notify_info_message("Updating scenario tags")
        EntityTagList.delete_by_entity(TagEntityType.SCENARIO, scenario_id)

        if self._origin_lab_id:
            for tag in tags:
                tag.set_external_lab_origin(self._origin_lab_id)

        entity_tags = EntityTagList(TagEntityType.SCENARIO, scenario_id)
        entity_tags.add_tags(tags)

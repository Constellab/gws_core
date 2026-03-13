import resource

from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.db.gws_core_db_manager import GwsCoreDbManager
from gws_core.entity_navigator.entity_navigator_service import EntityNavigatorService
from gws_core.external_lab.external_lab_dto import ExternalLabWithUserInfo
from gws_core.process.process_model import ProcessModel
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.protocol.protocol_proxy import ProtocolProxy
from gws_core.resource.resource_builder import (
    ResourceBuilder,
    ResourceDtoBuilder,
    ResourceZipBuilder,
)
from gws_core.resource.resource_loader import ResourceLoader
from gws_core.resource.resource_model import ResourceModel
from gws_core.scenario.scenario import Scenario
from gws_core.scenario.scenario_id_mapper import ScenarioIdMapper
from gws_core.scenario.scenario_loader import ScenarioLoader
from gws_core.scenario.scenario_zipper import ScenarioExportPackage
from gws_core.share.shared_dto import SharedEntityMode, ShareEntityCreateMode
from gws_core.share.shared_scenario import SharedScenario
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.tag import Tag
from gws_core.tag.tag_entity_type import TagEntityType
from gws_core.task.task_model import TaskModel
from gws_core.user.current_user_service import CurrentUserService


class ScenarioBuilder:
    """
    Builds a local scenario from an already-downloaded ``ScenarioExportPackage`` and a mapping
    of resource zip file paths.

    The class is responsible for:
    - Loading each zip file into a ``Resource`` object via ``ResourceZipBuilder``
    - Creating ``ResourceDtoBuilder`` instances for metadata-only resources
    - Running ``ScenarioLoader`` to prepare the scenario and protocol model
    - Persisting the scenario, protocol, resource models, tags, and shared-entity records to the DB

    This separation from ``ScenarioDownloader`` (which handles the HTTP/download phase) allows the
    build logic to be tested independently — e.g. to exercise "Skip if exists" without making
    any HTTP calls.

    Usage::

        builder = ScenarioBuilder(
            scenario_info=package,
            resource_zip_paths={resource_id: "/tmp/resource_abc.zip"},
            origin=external_lab_info,
        )
        try:
            scenario = builder.build()
        finally:
            builder.cleanup()
    """

    _scenario_info: ScenarioExportPackage
    _resource_zip_paths: dict[str, str]
    _origin: ExternalLabWithUserInfo
    _create_mode: ShareEntityCreateMode
    _message_dispatcher: MessageDispatcher | None
    _skip_resource_tags: bool
    _skip_scenario_tags: bool
    _id_mapper: ScenarioIdMapper

    # Internal state populated during build
    _resource_builders: dict[str, ResourceBuilder]

    def __init__(
        self,
        scenario_info: ScenarioExportPackage,
        resource_zip_paths: dict[str, str],
        origin: ExternalLabWithUserInfo,
        create_mode: ShareEntityCreateMode,
        message_dispatcher: MessageDispatcher | None = None,
        skip_resource_tags: bool = False,
        skip_scenario_tags: bool = False,
    ):
        self._scenario_info = scenario_info
        self._resource_zip_paths = resource_zip_paths
        self._origin = origin
        self._create_mode = create_mode
        self._message_dispatcher = message_dispatcher
        self._skip_resource_tags = skip_resource_tags
        self._skip_scenario_tags = skip_scenario_tags
        self._id_mapper = ScenarioIdMapper(create_mode)

        self._resource_builders = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @GwsCoreDbManager.transaction()
    def build(self) -> Scenario:
        """
        Load resources from zip files and build (or update) the scenario in the DB.

        In ``KEEP_ID`` mode, if a scenario with the same ID already exists in
        the database the builder automatically switches to **update mode**:
        scenario metadata is copied over, unused processes are deleted, rerun
        processes are reset, and the new protocol is saved on top of the
        existing one.

        :return: The created or updated Scenario.
        """
        scenario_loader = self._load_scenario()

        self._load_resources(scenario_loader)

        return self._build_scenario(scenario_loader)

    # ------------------------------------------------------------------
    # Internal steps
    # ------------------------------------------------------------------

    def _load_resources(
        self,
        scenario_loader: ScenarioLoader,
    ) -> None:
        """Create resource builders for each resource in the scenario.

        For resources with a zip path, creates a ResourceZipBuilder and loads the resource.
        For metadata-only resources, creates a ResourceDtoBuilder.
        """
        # Get all resource DTOs from the scenario metadata
        resource_dtos = scenario_loader.get_main_resource_model_dtos()

        for dto in resource_dtos:
            resource_id = dto.id
            if resource_id in self._resource_zip_paths:
                # Zip content available — create ResourceZipBuilder
                zip_path = self._resource_zip_paths[resource_id]
                resource_loader = ResourceLoader.from_compress_file(
                    zip_path, skip_tags=self._skip_resource_tags, id_mapper=self._id_mapper
                )
                builder = ResourceZipBuilder(
                    resource_loader=resource_loader,
                    origin=self._origin,
                    id_mapper=self._id_mapper,
                    skip_resource_tags=self._skip_resource_tags,
                    message_dispatcher=self._message_dispatcher,
                )
                self._resource_builders[resource_id] = builder
            else:
                # Metadata only — create ResourceDtoBuilder
                builder = ResourceDtoBuilder(
                    resource_model_dto=dto,
                    origin=self._origin,
                    id_mapper=self._id_mapper,
                    skip_resource_tags=self._skip_resource_tags,
                    message_dispatcher=self._message_dispatcher,
                )
                self._resource_builders[resource_id] = builder

    def _load_scenario(self) -> ScenarioLoader:
        """Initialise and run ScenarioLoader over the scenario export package."""
        self._log_info("Loading the scenario")
        loader = ScenarioLoader(self._scenario_info, self._message_dispatcher)
        loader.load_scenario()
        return loader

    def _build_scenario(
        self,
        scenario_loader: ScenarioLoader,
    ) -> Scenario:
        self._log_info("Building the scenario")

        scenario = scenario_loader.get_scenario()
        protocol_model = scenario_loader.get_protocol_model()

        update_mode = False

        # In KEEP_ID mode, check if the scenario already exists to enter update mode
        if self._create_mode == ShareEntityCreateMode.KEEP_ID:
            existing_scenario = Scenario.get_by_id(scenario_loader.get_scenario().id)
            if existing_scenario is not None:
                scenario, protocol_model = self._update_scenario(
                    scenario, protocol_model, existing_scenario
                )
                update_mode = True

        # Create resource models from metadata (content_is_deleted=True)
        self._log_info("Creating resource models from metadata")

        resource_builders: dict[str, ResourceBuilder] = self._resource_builders
        self._id_mapper.apply_new_ids(protocol_model, scenario)

        # make the resource_builder using new IDs as keys instead of old IDs, to be able to find them when saving resources
        resource_builders = {
            (self._id_mapper.generate_new_id(old_id)): builder
            for old_id, builder in self._resource_builders.items()
        }

        # Track which resource models have been saved to DB
        # Collect saved ResourceModel instances by ID to update port references later
        saved_models_by_id: dict[str, ResourceModel] = {}

        # Save all protocol input resources first
        for resource_model_id in protocol_model.get_input_resource_model_ids():
            resource_builder = resource_builders.get(resource_model_id)
            if resource_builder is None:
                raise Exception(
                    f"Protocol input resource with id '{resource_model_id}' not found in resource builders. "
                    "All protocol input resources must have a corresponding builder to ensure they are saved before the scenario and protocol."
                )
            self._save_builder_and_collect(resource_builder, saved_models_by_id)

        scenario.save()

        if update_mode:
            db_protocol_model = ProtocolModel.get_by_id_and_check(protocol_model.id)
            protocol_model = self._update_protocol_model(db_protocol_model, protocol_model)
        else:
            protocol_model.save_full()

        if not self._skip_scenario_tags:
            self._save_scenario_tags(scenario.id, scenario_loader.get_tags())
        else:
            self._log_info("Skipping scenario tags")

        # Save all the TaskInputModel and remaining resource in the correct order
        for process_model in protocol_model.get_all_processes_flatten_sort_by_start_date():
            if isinstance(process_model, TaskModel):
                for port in process_model.outputs.ports.values():
                    resource_model_id = port.get_resource_model_id()
                    if resource_model_id and resource_model_id not in saved_models_by_id:
                        resource_builder = resource_builders.get(resource_model_id)
                        if resource_builder is None:
                            raise Exception(
                                f"Resource with id '{resource_model_id}' not found in resource builders. "
                                "All protocol output resources must have a corresponding builder to ensure TaskInputModel records can be created."
                            )
                        self._save_builder_and_collect(resource_builder, saved_models_by_id)
                process_model.save_input_resources()

        # Create the shared entity info
        self._log_info("Storing the scenario origin info")
        SharedScenario.create_from_lab_info(
            scenario.id,
            SharedEntityMode.RECEIVED,
            self._origin,
            CurrentUserService.get_and_check_current_user(),
        )

        return scenario

    def _update_scenario(
        self,
        new_scenario: Scenario,
        new_protocol_model: ProtocolModel,
        existing_scenario: Scenario,
    ) -> tuple[Scenario, ProtocolModel]:
        """Update an existing scenario in place from the loaded scenario data.

        1. Updates scenario metadata via ``copy_from_and_save``
        2. Removes processes that no longer exist in the new protocol
        3. Resets processes whose output resources have changed (rerun detection)
        4. Saves the new protocol model (adds new processes / updates graph)
        """
        self._log_info("Updating the existing scenario")

        # 1. Update scenario metadata
        existing_scenario.copy_from_and_save(new_scenario)

        # 2. Update protocol: remove unused processes & reset rerun processes
        existing_protocol = existing_scenario.protocol_model
        self._update_protocol(existing_protocol, new_protocol_model)

        return existing_scenario, new_protocol_model

    def _update_protocol(
        self,
        existing_protocol: ProtocolModel,
        new_protocol: ProtocolModel,
    ) -> None:
        """Diff existing and new protocols: delete removed processes, reset rerun ones."""
        existing_processes_ids = [
            process.id
            for process in existing_protocol.get_all_processes_flatten_sort_by_start_date()
        ]
        new_processes_ids = [
            process.id for process in new_protocol.get_all_processes_flatten_sort_by_start_date()
        ]

        protocol_proxy = ProtocolProxy(existing_protocol)

        # Delete processes that exist in existing but not in new
        for existing_process_id in existing_processes_ids:
            existing_process = protocol_proxy.get_process_by_id(existing_process_id)
            if existing_process is None:
                continue  # Process already deleted by previous iteration, skip
            parent_protocol = existing_process.parent_protocol
            if not parent_protocol:
                continue

            # check if the process still exist because it might have been deleted by previous delete
            if existing_process_id not in new_processes_ids:
                self._log_info(f"Deleting unused process '{existing_process_id}'")
                parent_protocol.delete_process(existing_process.instance_name)
                protocol_proxy.refresh()

            # if the process exist in both protocol
            # check if it was rerun by comparing the output resource ids
            else:
                new_process = new_protocol.get_process_by_id(existing_process_id)
                if not new_process:
                    continue
                if self._process_was_rerun(existing_process.get_model(), new_process):
                    self._log_info(f"Resetting rerun process '{existing_process_id}'")
                    existing_process.reset_process()
                    protocol_proxy.refresh()

    def _process_was_rerun(
        self,
        existing_process: ProcessModel,
        new_process: ProcessModel,
    ) -> bool:
        """Check if a process was rerun by comparing output resource IDs."""
        for port_name, existing_port in existing_process.outputs.ports.items():
            new_port = new_process.outputs.ports.get(port_name)
            if new_port is None:
                continue
            if existing_port.get_resource_model_id() != new_port.get_resource_model_id():
                return True
        return False

    def _update_protocol_model(
        self, db_protocol_model: ProtocolModel, new_protocol_model: ProtocolModel
    ) -> ProtocolModel:
        """Save the new protocol model on top of the existing one to update the graph with new/updated processes."""
        # UPDATE: processes that exist in both
        db_processes = dict(db_protocol_model.processes)
        for process_instance_name, new_process in new_protocol_model.processes.items():
            if process_instance_name in db_processes:
                db_process = db_processes[process_instance_name]

                if isinstance(db_process, ProtocolModel) and isinstance(new_process, ProtocolModel):
                    db_process.copy_from_and_save(new_process)
                    self._update_protocol(db_process, new_process)
                else:
                    db_process.copy_from_and_save(new_process)

            # ADD: processes in new but not in old
            if process_instance_name not in db_processes:
                # self._message_dispatcher.notify_info_message(
                #     f"Adding new process '{new_process.instance_name}'"
                # )
                # TODO to fix
                # Generate a fresh ID to avoid conflicts with existing DB records
                new_process.id = new_process.id
                new_process.set_parent_protocol(db_protocol_model)
                new_process.set_scenario(db_protocol_model.scenario)
                new_process.save_full()
                db_protocol_model.add_process_model(
                    new_process, instance_name=process_instance_name
                )

        # TODO this is not great
        # Reload processes from DB after removals
        db_protocol_model.reload_graph()

        # Update protocol graph structure (connectors, interfaces, outerfaces, layout)
        db_protocol_model.copy_graph_from_and_save(new_protocol_model)

        return db_protocol_model

    def _save_builder_and_collect(
        self,
        resource_builder: ResourceBuilder,
        saved_models_by_id: dict[str, ResourceModel],
    ) -> None:
        """Save a resource builder and collect the main and children models into the map."""
        resource_model = resource_builder.save()
        saved_models_by_id[resource_model.id] = resource_model
        for child_model in resource_builder.get_children_resource_models():
            saved_models_by_id[child_model.id] = child_model

    def _save_scenario_tags(self, scenario_id: str, tags: list[Tag]) -> None:
        self._log_info("Saving the scenario tags")

        for tag in tags:
            tag.set_external_lab_origin(self._origin.lab.id)

        try:
            entity_tags = EntityTagList(TagEntityType.SCENARIO, scenario_id)
            entity_tags.add_tags(tags)
        except Exception as err:
            raise Exception(
                "Error while saving scenario tags. You can skip tags saving in the config. "
                + str(err)
            ) from err

    def _log_info(self, message: str) -> None:
        if self._message_dispatcher:
            self._message_dispatcher.notify_info_message(message)

    def cleanup(self) -> None:
        """Delete temporary resource folders created during zip extraction. Always call this."""
        for builder in self._resource_builders.values():
            builder.cleanup()

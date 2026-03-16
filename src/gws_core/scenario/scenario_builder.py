from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.db.gws_core_db_manager import GwsCoreDbManager
from gws_core.external_lab.external_lab_dto import ExternalLabWithUserInfo
from gws_core.process.process_model import ProcessModel
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.protocol.protocol_proxy import ProtocolProxy
from gws_core.resource.resource_builder import (
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
    - Creating ``ResourceDtoBuilder`` instances for all resources (shell models)
    - Running ``ScenarioLoader`` to prepare the scenario and protocol model
    - Persisting the scenario, protocol, shell resource models, tags, and shared-entity records
      to the DB inside a single transaction
    - After the transaction, filling zip-backed resources with their actual content
      via ``ResourceZipBuilder``

    This separation from ``ScenarioDownloader`` (which handles the HTTP/download phase) allows the
    build logic to be tested independently — e.g. to exercise "Skip if exists" without making
    any HTTP calls.

    **Build flow — phase 1 (transaction)**:

    1. ``_load_scenario`` — parse the export package via ``ScenarioLoader``.
    2. ``_load_resource_dtos`` — create a ``ResourceDtoBuilder`` for every
       resource (both zip-backed and metadata-only).
    3. ``_build_scenario`` (in transaction) — remap IDs, save shell resource
       models, persist the scenario and protocol (``save_full``), save
       remaining shell resources in execution order, then record tags and
       shared-entity origin.

    **Build flow — phase 2 (after transaction)**:

    4. ``_fill_zip_resources`` — for each resource with a zip file, create a
       ``ResourceZipBuilder`` and fill the shell resource with actual content.

    **Update mode** (``KEEP_ID`` and a scenario with the same ID already exists):

    Steps 1–2 are identical. Inside ``_build_scenario``:

    3a. ``_update_scenario`` — copy metadata onto the existing scenario, then
        call ``_sync_existing_processes`` to diff the old and new protocols
        (delete removed processes, reset rerun ones).
    3b. After saving the scenario, call ``_merge_protocol_into_db`` to
        reconcile the DB protocol: update existing processes, add new ones,
        reload the graph, and copy the new graph structure (connectors,
        interfaces, outerfaces, layout).
    3c. Save remaining shell resources, tags, and shared-entity origin as in
        creation mode.
    3d. Phase 2 then fills zip-backed resources as usual.

    Usage::

        builder = ScenarioBuilder(
            scenario_info=package,
            origin=external_lab_info,
        )
        scenario = builder.build()
        builder.fill_zip_resources({resource_id: "/tmp/resource_abc.zip"})
    """

    _scenario_info: ScenarioExportPackage
    _origin: ExternalLabWithUserInfo
    _create_mode: ShareEntityCreateMode
    _message_dispatcher: MessageDispatcher
    _skip_resource_tags: bool
    _skip_scenario_tags: bool
    _id_mapper: ScenarioIdMapper

    def __init__(
        self,
        scenario_info: ScenarioExportPackage,
        origin: ExternalLabWithUserInfo,
        create_mode: ShareEntityCreateMode,
        message_dispatcher: MessageDispatcher | None = None,
        skip_resource_tags: bool = False,
        skip_scenario_tags: bool = False,
    ):
        self._scenario_info = scenario_info
        self._origin = origin
        self._create_mode = create_mode
        self._message_dispatcher = message_dispatcher or MessageDispatcher()
        self._skip_resource_tags = skip_resource_tags
        self._skip_scenario_tags = skip_scenario_tags
        self._id_mapper = ScenarioIdMapper(create_mode)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build(self) -> Scenario:
        """
        Build (or update) the scenario in the DB inside a transaction.

        Creates shell resource models (``ResourceDtoBuilder``) for every
        resource and persists the scenario, protocol, and shell resources
        atomically. Call ``fill_zip_resources()`` afterwards to fill
        zip-backed resources with their actual content.

        In ``KEEP_ID`` mode, if a scenario with the same ID already exists in
        the database the builder automatically switches to **update mode**:
        scenario metadata is copied over, unused processes are deleted, rerun
        processes are reset, and the new protocol is saved on top of the
        existing one.

        :return: The created or updated Scenario.
        """
        scenario_loader = self._load_scenario()

        return self._build_scenario(scenario_loader)

    # ------------------------------------------------------------------
    # Internal steps
    # ------------------------------------------------------------------

    def _load_resource_dtos(
        self,
        scenario_loader: ScenarioLoader,
    ) -> dict[str, ResourceDtoBuilder]:
        """Create a ``ResourceDtoBuilder`` for every resource in the scenario.

        All resources — whether they have zip content or not — are first
        created as shell models from their DTO metadata. Zip-backed resources
        will have their content filled in a second phase after the scenario
        transaction completes.

        :return: A dict mapping original resource IDs to their builders.
        """
        resource_dtos = scenario_loader.get_main_resource_model_dtos()

        resource_dto_builders: dict[str, ResourceDtoBuilder] = {}
        for dto in resource_dtos:
            builder = ResourceDtoBuilder(
                resource_model_dto=dto,
                origin=self._origin,
                id_mapper=self._id_mapper,
                skip_resource_tags=self._skip_resource_tags,
                message_dispatcher=self._message_dispatcher,
            )
            resource_dto_builders[self._id_mapper.generate_new_id(dto.id)] = builder
        return resource_dto_builders

    def _load_scenario(self) -> ScenarioLoader:
        """Initialise and run ScenarioLoader over the scenario export package."""
        self._log_info("Loading the scenario")
        loader = ScenarioLoader(self._scenario_info, self._message_dispatcher)
        loader.load_scenario()
        return loader

    @GwsCoreDbManager.transaction()
    def _build_scenario(
        self,
        scenario_loader: ScenarioLoader,
    ) -> Scenario:
        """Build (or update) the scenario with shell resources inside a single transaction.

        All resources are saved as shell models (``content_is_deleted=True``)
        via their ``ResourceDtoBuilder``. Zip content is filled separately
        after the transaction by ``_fill_zip_resources``.
        """
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
        self._log_info("Creating shell resource models from metadata")

        self._id_mapper.apply_new_ids(protocol_model, scenario)

        resource_dto_builders = self._load_resource_dtos(scenario_loader)

        # Track which resource models have been saved to DB
        saved_models_by_id: dict[str, ResourceModel] = {}

        # Save all protocol input resources first
        for resource_model_id in protocol_model.get_input_resource_model_ids():
            resource_builder = resource_dto_builders.get(resource_model_id)
            if resource_builder is None:
                raise Exception(
                    f"Protocol input resource with id '{resource_model_id}' not found in resource builders. "
                    "All protocol input resources must have a corresponding builder to ensure they are saved before the scenario and protocol."
                )
            self._save_builder_and_collect(resource_builder, saved_models_by_id)

        scenario.save()

        # If we are in update mode, we update the protocol manually
        if update_mode:
            db_protocol_model = ProtocolModel.get_by_id_and_check(protocol_model.id)
            protocol_model = self._merge_protocol_into_db(db_protocol_model, protocol_model)
        else:
            protocol_model.save_full()

        if not self._skip_scenario_tags:
            self._save_scenario_tags(scenario.id, scenario_loader.get_tags())
        else:
            self._log_info("Skipping scenario tags")

        # Save all the TaskInputModel and remaining resources in the correct order
        for process_model in protocol_model.get_all_processes_flatten_sort_by_start_date():
            if isinstance(process_model, TaskModel):
                for port in process_model.outputs.ports.values():
                    resource_model_id = port.get_resource_model_id()
                    if resource_model_id and resource_model_id not in saved_models_by_id:
                        resource_builder = resource_dto_builders.get(resource_model_id)
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
        self._sync_existing_processes(existing_protocol, new_protocol_model)

        return existing_scenario, new_protocol_model

    def _sync_existing_processes(
        self,
        existing_protocol: ProtocolModel,
        new_protocol: ProtocolModel,
    ) -> None:
        """Synchronise the existing protocol's processes with the new protocol definition.

        Iterates over every process in the existing protocol and compares it
        against the new protocol's process list:

        - **Removed processes** (present in existing but absent in new) are
          deleted from the existing protocol via their parent protocol.
        - **Rerun processes** (present in both but with different output
          resource IDs) are reset so they will be re-executed.

        The method operates through a ``ProtocolProxy`` which is refreshed
        after each mutation to keep the in-memory graph consistent.

        This method is called recursively by ``_merge_protocol_into_db`` for
        nested sub-protocols.
        """
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

    def _merge_protocol_into_db(
        self, db_protocol_model: ProtocolModel, new_protocol_model: ProtocolModel
    ) -> ProtocolModel:
        """Merge the new protocol definition into the existing DB protocol.

        Reconciles the persisted protocol with the incoming one in three phases:

        1. **Update / add processes** — for each process in ``new_protocol_model``:
           - If it already exists in the DB protocol, its metadata is copied
             over. For nested sub-protocols, ``_sync_existing_processes`` is
             called recursively to propagate deletions and resets downward.
           - If it is new, it is attached to the DB protocol, linked to the
             parent scenario, fully saved, and registered as a child process.
        2. **Reload graph** — the DB protocol reloads its process map from the
           database so that any deletions performed by
           ``_sync_existing_processes`` are reflected in memory.
        3. **Copy graph structure** — connectors, interfaces, outerfaces, and
           layout are copied from ``new_protocol_model`` onto the DB protocol
           and persisted.

        :param db_protocol_model: The protocol currently stored in the DB.
        :param new_protocol_model: The freshly loaded protocol to merge in.
        :return: The updated ``db_protocol_model`` after merge.
        """
        # UPDATE: processes that exist in both
        db_processes = dict(db_protocol_model.processes)
        for process_instance_name, new_process in new_protocol_model.processes.items():
            if process_instance_name in db_processes:
                db_process = db_processes[process_instance_name]

                if isinstance(db_process, ProtocolModel) and isinstance(new_process, ProtocolModel):
                    db_process.copy_from_and_save(new_process)
                    self._sync_existing_processes(db_process, new_process)
                else:
                    db_process.copy_from_and_save(new_process)

            # ADD: processes in new but not in old
            if process_instance_name not in db_processes:
                self._log_info(f"Adding new process '{new_process.instance_name}'")
                new_process.id = new_process.id
                new_process.set_parent_protocol(db_protocol_model)
                new_process.set_scenario(db_protocol_model.scenario)
                new_process.save_full()
                db_protocol_model.add_process_model(
                    new_process, instance_name=process_instance_name
                )

        # Reload processes from DB after removals
        db_protocol_model.reload_graph()

        # Update protocol graph structure (connectors, interfaces, outerfaces, layout)
        db_protocol_model.copy_graph_from_and_save(new_protocol_model)

        return db_protocol_model

    def fill_zip_resources(self, resource_zip_paths: dict[str, str]) -> None:
        """Fill shell resources that have zip content with their actual data.

        Should be called after ``build()`` completes. For each resource
        that has a corresponding zip file, creates a ``ResourceZipBuilder``
        and saves the content into the existing shell resource model.

        :param resource_zip_paths: Mapping of resource IDs to zip file paths.
        """
        if not resource_zip_paths:
            return

        self._log_info("Filling resource content from zip files")

        for zip_path in resource_zip_paths.values():
            resource_loader = ResourceLoader.from_compress_file(
                zip_path, skip_tags=self._skip_resource_tags, id_mapper=self._id_mapper
            )
            zip_builder = ResourceZipBuilder(
                resource_loader=resource_loader,
                origin=self._origin,
                id_mapper=self._id_mapper,
                skip_resource_tags=self._skip_resource_tags,
                message_dispatcher=self._message_dispatcher,
            )
            zip_builder.save()

    def _save_builder_and_collect(
        self,
        resource_builder: ResourceDtoBuilder,
        saved_models_by_id: dict[str, ResourceModel],
    ) -> None:
        """Save a resource dto builder and collect the model into the map."""
        resource_model = resource_builder.save()
        saved_models_by_id[resource_model.id] = resource_model

    def _save_scenario_tags(self, scenario_id: str, tags: list[Tag]) -> None:
        self._log_info("Saving the scenario tags")

        entity_tags = EntityTagList.find_by_entity(TagEntityType.SCENARIO, scenario_id)
        for tag in tags:
            tag.set_external_lab_origin(self._origin.lab.id)
            try:
                if not entity_tags.has_tag(tag):
                    entity_tags.add_tag(tag)
            except Exception as err:
                self._message_dispatcher.notify_error_message(
                    f"Error while saving tag '{tag.key}={tag.value}': {err}. "
                    "You can skip tags saving in the config."
                )

    def _log_info(self, message: str) -> None:
        if self._message_dispatcher:
            self._message_dispatcher.notify_info_message(message)

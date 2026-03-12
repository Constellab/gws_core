from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.db.gws_core_db_manager import GwsCoreDbManager
from gws_core.external_lab.external_lab_dto import ExternalLabWithUserInfo
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.resource.id_mapper import IdMapper
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
            scenario = builder.build(create_mode=ShareEntityCreateMode.KEEP_ID)
        finally:
            builder.cleanup()
    """

    _scenario_info: ScenarioExportPackage
    _resource_zip_paths: dict[str, str]
    _origin: ExternalLabWithUserInfo
    _message_dispatcher: MessageDispatcher | None
    _skip_resource_tags: bool

    # Internal state populated during build
    _resource_builders: dict[str, ResourceBuilder]

    def __init__(
        self,
        scenario_info: ScenarioExportPackage,
        resource_zip_paths: dict[str, str],
        origin: ExternalLabWithUserInfo,
        message_dispatcher: MessageDispatcher | None = None,
        skip_resource_tags: bool = False,
    ):
        self._scenario_info = scenario_info
        self._resource_zip_paths = resource_zip_paths
        self._origin = origin
        self._message_dispatcher = message_dispatcher
        self._skip_resource_tags = skip_resource_tags

        self._resource_builders = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @GwsCoreDbManager.transaction()
    def build(
        self,
        skip_scenario_tags: bool = False,
        create_mode: ShareEntityCreateMode = ShareEntityCreateMode.KEEP_ID,
    ) -> Scenario:
        """
        Load resources from zip files and build (or update) the scenario in the DB.

        :param skip_scenario_tags: If True, scenario tags are not saved.
        :param create_mode: KEEP_ID preserves original IDs; NEW_ID assigns fresh UUIDs.
        :return: The created or updated Scenario.
        """
        scenario_loader = self._load_scenario()

        self._load_resources(create_mode, scenario_loader)

        return self._build_scenario(scenario_loader, skip_scenario_tags, create_mode)

    def cleanup(self) -> None:
        """Delete temporary resource folders created during zip extraction. Always call this."""
        for builder in self._resource_builders.values():
            builder.cleanup()

    # ------------------------------------------------------------------
    # Internal steps
    # ------------------------------------------------------------------

    def _load_resources(
        self,
        create_mode: ShareEntityCreateMode,
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
                    zip_path, skip_tags=self._skip_resource_tags, mode=create_mode
                )
                builder = ResourceZipBuilder(
                    resource_loader=resource_loader,
                    origin=self._origin,
                    skip_resource_tags=self._skip_resource_tags,
                    create_mode=create_mode,
                    message_dispatcher=self._message_dispatcher,
                )
                self._resource_builders[resource_id] = builder
            else:
                # Metadata only — create ResourceDtoBuilder
                builder = ResourceDtoBuilder(
                    resource_model_dto=dto,
                    origin=self._origin,
                    skip_resource_tags=self._skip_resource_tags,
                    create_mode=create_mode,
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
        skip_scenario_tags: bool,
        create_mode: ShareEntityCreateMode,
    ) -> Scenario:
        self._log_info("Building the scenario")

        scenario = scenario_loader.get_scenario()
        protocol_model = scenario_loader.get_protocol_model()

        # Create resource models from metadata (content_is_deleted=True)
        self._log_info("Creating resource models from metadata")
        metadata_resource_models = scenario_loader.load_resource_models()

        id_mapper = ScenarioIdMapper()
        resource_builders: dict[str, ResourceBuilder] = self._resource_builders
        if create_mode == ShareEntityCreateMode.NEW_ID:
            id_mapper.apply_new_ids(
                protocol_model, list(metadata_resource_models.values()), scenario
            )

            #######################
            ### TODO to improve
            #######################
            # make the resource_builder using new IDs as keys instead of old IDs, to be able to find them when saving resources
            resource_builders = {
                (id_mapper.get_new_id(old_id) or old_id): builder
                for old_id, builder in self._resource_builders.items()
            }

        # Track which resource models have been saved to DB
        saved_resource_ids: set[str] = set()
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
            resource_builder.set_id_mapper(id_mapper)
            resource_model = resource_builder.save()
            saved_resource_ids.add(resource_model.id)
            saved_models_by_id[resource_model.id] = resource_model

        scenario.save()
        protocol_model.save_full()

        if not skip_scenario_tags:
            self._save_scenario_tags(scenario.id, scenario_loader.get_tags())
        else:
            self._log_info("Skipping scenario tags")

        #######################
        ### TODO use builder instead of metadata_resource_models
        #######################

        # Save remaining resources
        for metadata_rm in metadata_resource_models.values():
            if metadata_rm.id not in saved_resource_ids:
                resource_builder = resource_builders.get(metadata_rm.id)
                if resource_builder is None:
                    raise Exception(
                        f"Resource with id '{metadata_rm.id}' not found in resource builders. "
                        "All resources must have a corresponding builder."
                    )
                resource_builder.set_id_mapper(id_mapper)
                saved_rm = resource_builder.save()
                saved_resource_ids.add(saved_rm.id)
                saved_models_by_id[saved_rm.id] = saved_rm

        #######################
        ### TODO use scenario mapper id
        #######################

        # Update port references again for any remaining resources just saved
        self._update_port_resource_models(protocol_model, saved_models_by_id)

        # Save all the TaskInputModel
        for process_model in protocol_model.get_all_processes_flatten_sort_by_start_date():
            if isinstance(process_model, TaskModel):
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

    @staticmethod
    def _update_port_resource_models(
        protocol: ProtocolModel,
        saved_models_by_id: dict[str, ResourceModel],
    ) -> None:
        """Replace port resource model references with the actual saved instances.

        After ResourceBuilder.save() creates its own ResourceModel instances,
        the ports still hold the old metadata-only instances that were never persisted.
        This walks all ports and swaps in the saved instances so that
        save_input_resources() sees is_saved() == True.
        """
        for process in protocol.processes.values():
            for port in process.inputs.ports.values():
                rm_id = port.get_resource_model_id()
                if rm_id and rm_id in saved_models_by_id:
                    port.set_resource_model(saved_models_by_id[rm_id])
            for port in process.outputs.ports.values():
                rm_id = port.get_resource_model_id()
                if rm_id and rm_id in saved_models_by_id:
                    port.set_resource_model(saved_models_by_id[rm_id])
            if isinstance(process, ProtocolModel):
                ScenarioBuilder._update_port_resource_models(process, saved_models_by_id)

    def _save_resources(self, id_mapper: IdMapper | None = None) -> None:
        """Save all resources via their builders."""
        self._log_info("Saving the resources")

        for resource_builder in self._resource_builders.values():
            if id_mapper:
                resource_builder.set_id_mapper(id_mapper)
            resource_builder.save()

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

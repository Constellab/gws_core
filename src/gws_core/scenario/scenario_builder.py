import resource

from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.db.gws_core_db_manager import GwsCoreDbManager
from gws_core.external_lab.external_lab_dto import ExternalLabWithUserInfo
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

    @staticmethod
    def _save_builder_and_collect(
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
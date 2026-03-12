from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.db.gws_core_db_manager import GwsCoreDbManager
from gws_core.external_lab.external_lab_dto import ExternalLabWithUserInfo
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.resource.resource_builder import ImportedResource, ResourceBuilder
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
from gws_core.task.plug.input_task import InputTask
from gws_core.task.task_model import TaskModel
from gws_core.user.current_user_service import CurrentUserService


class ScenarioBuilder:
    """
    Builds a local scenario from an already-downloaded `ScenarioExportPackage` and a list of
    resource zip file paths.

    The class is responsible for:
    - Loading each zip file into a `Resource` object via `ResourceBuilder`
    - Running `ScenarioLoader` to prepare the scenario and protocol model
    - Persisting the scenario, protocol, resource models, tags, and shared-entity records to the DB

    This separation from `ScenarioDownloader` (which handles the HTTP/download phase) allows the
    build logic to be tested independently — e.g. to exercise "Skip if exists" without making
    any HTTP calls.

    Usage::

        builder = ScenarioBuilder(
            scenario_info=package,
            resource_zip_paths=["/tmp/resource_abc.zip"],
            origin=external_lab_info,
        )
        try:
            scenario = builder.build(create_mode=ShareEntityCreateMode.KEEP_ID)
        finally:
            builder.cleanup()
    """

    _scenario_info: ScenarioExportPackage
    _resource_zip_paths: list[str]
    _origin: ExternalLabWithUserInfo
    _message_dispatcher: MessageDispatcher | None
    _skip_resource_tags: bool

    # Internal state populated during build
    _resource_builders: list[ResourceBuilder]
    _downloaded_resources: dict[str, ImportedResource]
    _root_resource_old_ids: set[str]

    def __init__(
        self,
        scenario_info: ScenarioExportPackage,
        resource_zip_paths: list[str],
        origin: ExternalLabWithUserInfo,
        message_dispatcher: MessageDispatcher | None = None,
        skip_resource_tags: bool = False,
    ):
        self._scenario_info = scenario_info
        self._resource_zip_paths = resource_zip_paths
        self._origin = origin
        self._message_dispatcher = message_dispatcher
        self._skip_resource_tags = skip_resource_tags

        self._resource_builders = []
        self._downloaded_resources = {}
        self._root_resource_old_ids = set()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @GwsCoreDbManager.transaction()
    def build(
        self,
        skip_scenario_tags: bool = False,
        create_mode: ShareEntityCreateMode = ShareEntityCreateMode.KEEP_ID,
        existing_scenario: Scenario | None = None,
    ) -> Scenario:
        """
        Load resources from zip files and build (or update) the scenario in the DB.

        :param skip_scenario_tags: If True, scenario tags are not saved.
        :param create_mode: KEEP_ID preserves original IDs; NEW_ID assigns fresh UUIDs.
        :param existing_scenario: Provide only in update mode.
        :return: The created or updated Scenario.
        """
        self._load_resources(create_mode)

        scenario_loader = self._load_scenario()

        return self._build_scenario(scenario_loader, skip_scenario_tags, create_mode)

    def cleanup(self) -> None:
        """Delete temporary resource folders created during zip extraction. Always call this."""
        for builder in self._resource_builders:
            builder.cleanup()

    # ------------------------------------------------------------------
    # Internal steps
    # ------------------------------------------------------------------

    def _load_resources(self, create_mode: ShareEntityCreateMode) -> None:
        """Load each zip file into an ImportedResource and populate _resource_models."""
        for zip_path in self._resource_zip_paths:
            resource_builder = ResourceBuilder(
                resource_zip_path=zip_path,
                origin=self._origin,
                skip_resource_tags=self._skip_resource_tags,
                create_mode=create_mode,
            )
            self._resource_builders.append(resource_builder)

            imported = resource_builder.load_resource()
            self._downloaded_resources[imported.old_id] = imported

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

        if create_mode == ShareEntityCreateMode.NEW_ID:
            self._apply_new_ids(protocol_model, metadata_resource_models, scenario)

        # Track which resource models have been saved to DB
        saved_resource_ids: set[str] = set()

        # Save all protocol input resources first
        for resource_model_id in protocol_model.get_input_resource_model_ids():
            # Check if the resource already exists in the DB
            existing_resource = ResourceModel.get_by_id(resource_model_id)
            if existing_resource:
                saved_resource_ids.add(resource_model_id)
                continue

            # search the resource by the actual resource model ID, the metadata_resource_models keys are old IDs but model.
            # id is the new ID in NEW_ID mode
            resource_model = next(
                (rm for rm in metadata_resource_models.values() if rm.id == resource_model_id),
                None,
            )
            if resource_model is None:
                raise Exception(
                    f"Input resource model with id '{resource_model_id}' not found in metadata. "
                    "All input resource models must be present in the metadata to ensure they are saved before filling content."
                )
            resource_model.save_full()
            saved_resource_ids.add(resource_model.id)

        scenario.save()
        protocol_model.save_full()

        if not skip_scenario_tags:
            self._save_scenario_tags(scenario.id, scenario_loader.get_tags())
        else:
            self._log_info("Skipping scenario tags")

        # Save remaining resources
        for resource_model in metadata_resource_models.values():
            if resource_model.id not in saved_resource_ids:
                resource_model.save_full()
                saved_resource_ids.add(resource_model.id)

        # Save all the TaskInputModel
        for process_model in protocol_model.get_all_processes_flatten_sort_by_start_date():
            if isinstance(process_model, TaskModel):
                process_model.save_input_resources()

        # Track old IDs of root-level resources to distinguish owned children
        # from resources referenced inside a ResourceListBase.
        self._root_resource_old_ids = set(metadata_resource_models.keys())

        # In NEW_ID mode, build old→new ID mapping for ResourceBuilders
        old_to_new_id: dict[str, str] = {}
        if create_mode == ShareEntityCreateMode.NEW_ID:
            for old_id, resource_model in metadata_resource_models.items():
                if old_id != resource_model.id:
                    old_to_new_id[old_id] = resource_model.id

        # Fill downloaded content into resource shells and create child models
        self._fill_resources_content(old_to_new_id)

        # Create the shared entity info
        self._log_info("Storing the scenario origin info")
        SharedScenario.create_from_lab_info(
            scenario.id,
            SharedEntityMode.RECEIVED,
            self._origin,
            CurrentUserService.get_and_check_current_user(),
        )

        return scenario

    def _apply_new_ids(
        self,
        protocol_model: ProtocolModel,
        metadata_resource_models: dict[str, ResourceModel],
        scenario: Scenario,
    ) -> None:
        """Replace all IDs with fresh UUIDs for NEW_ID mode."""
        id_mapper = ScenarioIdMapper()
        id_mapper.apply_new_ids(protocol_model, list(metadata_resource_models.values()), scenario)

    def _fill_resources_content(self, old_to_new_id: dict[str, str] | None = None) -> None:
        """Fill downloaded content into pre-created resource shells,
        create child resource models, and create TaskInputModel records."""
        self._log_info("Saving the resources")

        for resource_builder in self._resource_builders:
            if old_to_new_id:
                resource_builder.set_old_to_new_id_mapping(old_to_new_id)
            resource_builder.fill_resources_content(
                root_resource_old_ids=self._root_resource_old_ids
            )

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

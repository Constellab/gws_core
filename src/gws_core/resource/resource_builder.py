import uuid

from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.external_lab.external_lab_dto import ExternalLabWithUserInfo
from gws_core.resource.resource import Resource
from gws_core.resource.resource_dto import ResourceModelExportDTO, ResourceOrigin
from gws_core.resource.resource_loader import ResourceLoader
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.resource_model_loader import ResourceModelLoader
from gws_core.resource.resource_set.resource_list_base import ResourceListBase
from gws_core.scenario.scenario import Scenario
from gws_core.share.shared_dto import SharedEntityMode, ShareEntityCreateMode
from gws_core.share.shared_resource import SharedResource
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.tag import TagOrigin
from gws_core.tag.tag_entity_type import TagEntityType
from gws_core.tag.tag_list import TagList
from gws_core.task.task_model import TaskModel
from gws_core.user.current_user_service import CurrentUserService


class ImportedResource:
    old_id: str
    resource: Resource
    children: dict[str, Resource]

    def __init__(self, old_id: str, resource: Resource, children: dict[str, Resource]):
        self.old_id = old_id
        self.resource = resource
        self.children = children


class ResourceBuilder:
    """
    Builds and persists a single resource from an already-downloaded zip file.

    Responsibilities:
    - Loading the zip file into a `Resource` object via `ResourceLoader`
    - Loading `ResourceModel` shells from `ResourceModelExportDTO` metadata
    - Filling content into pre-created resource model shells
    - Saving the resource and its children to the DB
    - Recording shared-entity provenance

    This class is used by `ScenarioBuilder` to handle individual resource
    persistence, and can also be used standalone for resource imports.

    Usage::

        builder = ResourceBuilder(
            resource_zip_path="/tmp/resource_abc.zip",
            origin=external_lab_info,
        )
        try:
            imported = builder.load_resource(create_mode=ShareEntityCreateMode.KEEP_ID)
        finally:
            builder.cleanup()
    """

    _resource_zip_path: str
    _origin: ExternalLabWithUserInfo
    _skip_resource_tags: bool
    _create_mode: ShareEntityCreateMode

    # Internal state populated during load/build
    _resource_loader: ResourceLoader | None
    _imported_resource: ImportedResource | None
    # Mapping from old DTO ID to new ResourceModel ID (used in NEW_ID mode)
    _old_to_new_id: dict[str, str]

    def __init__(
        self,
        resource_zip_path: str,
        origin: ExternalLabWithUserInfo,
        skip_resource_tags: bool = False,
        create_mode: ShareEntityCreateMode = ShareEntityCreateMode.KEEP_ID,
    ):
        self._resource_zip_path = resource_zip_path
        self._origin = origin
        self._skip_resource_tags = skip_resource_tags
        self._create_mode = create_mode

        self._resource_loader = None
        self._imported_resource = None
        self._old_to_new_id = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_resource(self, create_mode: ShareEntityCreateMode) -> ImportedResource:
        """Load the zip file into an ImportedResource.

        :param create_mode: KEEP_ID preserves original IDs; NEW_ID assigns fresh UUIDs.
        :return: The loaded ImportedResource.
        """
        self._resource_loader = ResourceLoader.from_compress_file(
            self._resource_zip_path, skip_tags=self._skip_resource_tags, mode=create_mode
        )

        resource = self._resource_loader.load_resource()

        self._imported_resource = ImportedResource(
            self._resource_loader.get_main_resource_origin_id(),
            resource,
            self._resource_loader.get_generated_children_resources(),
        )

        return self._imported_resource

    def get_imported_resource(self) -> ImportedResource | None:
        """Return the imported resource loaded by `load_resource`, or None if not yet loaded."""
        return self._imported_resource

    def set_old_to_new_id_mapping(self, mapping: dict[str, str]) -> None:
        """Set the mapping from old resource IDs to new resource IDs.

        Used by ScenarioBuilder in NEW_ID mode where resource models are created
        with new IDs by ScenarioIdMapper before content is filled.
        """
        self._old_to_new_id = mapping

    @classmethod
    def from_loaded_resource_loader(
        cls,
        resource_loader: ResourceLoader,
        resource: Resource,
        origin: ExternalLabWithUserInfo,
        skip_resource_tags: bool = False,
        create_mode: ShareEntityCreateMode = ShareEntityCreateMode.KEEP_ID,
    ) -> "ResourceBuilder":
        """Create a ResourceBuilder from an already-loaded ResourceLoader and resource."""
        builder = cls(
            resource_zip_path="",
            origin=origin,
            skip_resource_tags=skip_resource_tags,
            create_mode=create_mode,
        )
        builder._resource_loader = resource_loader
        builder._imported_resource = ImportedResource(
            resource_loader.get_main_resource_origin_id(),
            resource,
            resource_loader.get_generated_children_resources(),
        )
        return builder

    def fill_resources_content(
        self,
        root_resource_old_ids: set[str] | None = None,
    ) -> None:
        """Fill downloaded content into pre-created resource shells,
        create child resource models, and create shared entity records.

        :param root_resource_old_ids: Old IDs of root-level resources. Children whose ID
            is in this set won't get parent_resource_id set (they are standalone resources
            referenced in a ResourceListBase). Pass None or empty set for standalone mode.
        """
        if self._imported_resource is None:
            raise Exception("No imported resource. Call load_resource() first.")

        old_resource_id = self._imported_resource.old_id
        self.save_resource_and_children(old_resource_id, root_resource_old_ids)

    def save_resource_and_children(
        self,
        old_resource_id: str | None,
        root_resource_old_ids: set[str] | None = None,
    ) -> ResourceModel | None:
        """Save a resource and its children to the DB.

        :param old_resource_id: The original resource ID from the export.
        :param task_model: The task model that generated this resource.
        :param scenario: The scenario this resource belongs to.
        :param root_resource_old_ids: Old IDs of root-level resources to distinguish
            owned children from standalone resources referenced in a ResourceListBase.
        :return: The saved ResourceModel, or None if old_resource_id is None.
        """
        if not old_resource_id:
            return None

        if root_resource_old_ids is None:
            root_resource_old_ids = set()

        resolved_id = self._resolve_resource_id(old_resource_id)
        existing_model = ResourceModel.get_by_id(resolved_id)

        if not existing_model:
            raise Exception(
                f"Resource model with id '{old_resource_id}' not found in the database. "
                "All resource models must be pre-created from metadata before saving content."
            )

        # If the resource model already exists with content, return it as-is
        if not existing_model.content_is_deleted:
            return existing_model

        downloaded_resource = self._get_downloaded_resource(old_resource_id)
        if not downloaded_resource:
            return existing_model

        # First save the children resources
        children_resource_models: list[ResourceModel] = []
        if len(downloaded_resource.children) > 0 and isinstance(
            downloaded_resource.resource, ResourceListBase
        ):
            new_children_resources: dict[str, Resource] = {}
            for child_old_id, child_resource in downloaded_resource.children.items():
                child_model = self._save_resource(
                    child_old_id,
                    child_resource,
                    existing_model.task_model,
                    existing_model.scenario,
                    port_name=existing_model.generated_by_port_name,
                )
                new_children_resources[child_resource.uid] = child_model.get_resource()
                if child_old_id not in root_resource_old_ids:
                    children_resource_models.append(child_model)
            downloaded_resource.resource.__set_r_field__(new_children_resources)

        resource_model = self._save_resource(
            old_resource_id,
            downloaded_resource.resource,
            existing_model.task_model,
            existing_model.scenario,
            existing_model.generated_by_port_name,
        )

        for child_model in children_resource_models:
            child_model.set_parent_and_save(resource_model.id)

        return resource_model

    def build_and_save_resource(
        self,
        message_dispatcher: MessageDispatcher | None = None,
    ) -> ResourceModel:
        """Build and save the resource and its children directly from zip metadata.

        Creates ResourceModel shells from the zip's ResourceModelExportDTO metadata,
        looking up existing resources in the DB. Then fills content into the shells.

        :param message_dispatcher: optional dispatcher for info messages
        :return: The saved main ResourceModel.
        """
        if self._imported_resource is None:
            raise Exception("No imported resource. Call load_resource() first.")
        if self._resource_loader is None:
            raise Exception("No resource loader available.")

        # Create/resolve ResourceModel shells for all resources from zip metadata
        for zip_resource in self._resource_loader.get_all_zip_resources():
            dto = zip_resource.resource_model_export
            self._resolve_or_create_resource_model(dto, message_dispatcher)

        # Use existing fill_resources_content logic
        self.fill_resources_content()

        # Return the main resource model
        main_id = self._resolve_resource_id(self._imported_resource.old_id)
        return ResourceModel.get_by_id_and_check(main_id)

    def cleanup(self) -> None:
        """Delete temporary resource folders created during zip extraction. Always call this."""
        if self._resource_loader:
            self._resource_loader.delete_resource_folder()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_or_create_resource_model(
        self,
        dto: ResourceModelExportDTO,
        message_dispatcher: MessageDispatcher | None = None,
    ) -> ResourceModel:
        """Resolve an existing ResourceModel from the DB or create a new shell from metadata.

        In KEEP_ID mode:
        - Resource doesn't exist: create shell via ResourceModelLoader, save it
        - Resource exists with content_is_deleted: update attributes, return (content filled later)
        - Resource exists with content: update attributes, return as-is

        In NEW_ID mode:
        - Always create a new shell with a fresh ID
        """
        # In NEW_ID mode, always create a new resource model with a new ID
        if self._create_mode == ShareEntityCreateMode.NEW_ID:
            resource_model = ResourceModelLoader(dto).load_resource_model(
                origin=ResourceOrigin.IMPORTED_FROM_LAB,
                message_dispatcher=message_dispatcher,
            )
            # Assign a new ID
            resource_model.id = str(uuid.uuid4())
            resource_model.parent_resource_id = (
                self._resolve_resource_id(dto.parent_resource_id)
                if dto.parent_resource_id
                else None
            )
            resource_model.save_full()
            # Track old->new ID mapping
            self._old_to_new_id[dto.id] = resource_model.id
            return resource_model

        existing = ResourceModel.get_by_id(dto.id)

        if existing is None:
            # Create a new shell from metadata
            resource_model = ResourceModelLoader(dto).load_resource_model(
                origin=ResourceOrigin.IMPORTED_FROM_LAB,
                message_dispatcher=message_dispatcher,
            )
            resource_model.save_full()
            return resource_model

        # Resource exists — update attributes from DTO
        self._update_resource_model_attributes(existing, dto, message_dispatcher)
        existing.save()
        return existing

    def _update_resource_model_attributes(
        self,
        resource_model: ResourceModel,
        dto: ResourceModelExportDTO,
        message_dispatcher: MessageDispatcher | None = None,
    ) -> None:
        """Update metadata attributes on an existing ResourceModel from DTO."""
        resource_model.name = dto.name
        resource_model.flagged = dto.flagged
        resource_model.style = dto.style
        resource_model.generated_by_port_name = dto.generated_by_port_name
        resource_model.origin = ResourceOrigin.IMPORTED_FROM_LAB

        # Resolve scenario and task_model (they might not exist in this lab)
        if dto.scenario and dto.task_model_id:
            existing_scenario = Scenario.get_by_id(dto.scenario.id)
            existing_task = TaskModel.get_by_id(dto.task_model_id)
            if existing_scenario and existing_task:
                resource_model.scenario = existing_scenario
                resource_model.task_model = existing_task
            else:
                dispatcher = message_dispatcher or MessageDispatcher()
                dispatcher.notify_info_message(
                    f"Resource '{dto.name}' references scenario '{dto.scenario.title}' "
                    f"and task model '{dto.task_model_id}' which could not be found. "
                    "Attributes updated without scenario/task link."
                )

    def _resolve_resource_id(self, old_resource_id: str) -> str:
        """Resolve an old resource ID to the actual DB ID.

        In NEW_ID mode, returns the mapped new ID. In KEEP_ID mode, returns the same ID.
        """
        return self._old_to_new_id.get(old_resource_id, old_resource_id)

    def _get_downloaded_resource(self, old_resource_id: str) -> ImportedResource | None:
        """Look up a downloaded resource by its old ID."""
        if self._imported_resource and self._imported_resource.old_id == old_resource_id:
            return self._imported_resource
        return None

    def _save_resource(
        self,
        old_resource_id: str,
        resource: Resource,
        task_model: TaskModel | None = None,
        scenario: Scenario | None = None,
        port_name: str | None = None,
        flagged: bool = False,
    ) -> ResourceModel:
        resolved_id = self._resolve_resource_id(old_resource_id)

        # In NEW_ID mode, only look up models we explicitly created/mapped.
        # Don't accidentally reuse original models still in the DB.
        existing_model: ResourceModel | None = None
        if (
            self._create_mode != ShareEntityCreateMode.NEW_ID
            or old_resource_id in self._old_to_new_id
        ):
            existing_model = ResourceModel.get_by_id(resolved_id)

        if existing_model and not existing_model.content_is_deleted:
            return existing_model

        try:
            if existing_model and existing_model.content_is_deleted:
                resource_model = existing_model.fill_content_from_resource(resource)

                # fill_content_from_resource doesn't save tags, do it here
                if resource.tags and isinstance(resource.tags, TagList):
                    user_origin = TagOrigin.current_user_origin()
                    entity_tags = EntityTagList(
                        TagEntityType.RESOURCE, resource_model.id, default_origin=user_origin
                    )
                    entity_tags.add_tags(resource.tags.get_tags())
            else:
                resource_model = ResourceModel.save_from_resource(
                    resource,
                    origin=ResourceOrigin.IMPORTED_FROM_LAB,
                    scenario=scenario,
                    task_model=task_model,
                    port_name=port_name,
                    flagged=flagged,
                )
        except Exception as err:
            raise Exception(
                f"Error while saving resource with old id '{old_resource_id}'. {str(err)}"
            ) from err

        SharedResource.create_from_lab_info(
            resource_model.id,
            SharedEntityMode.RECEIVED,
            self._origin,
            CurrentUserService.get_and_check_current_user(),
        )

        return resource_model

from abc import abstractmethod

from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.external_lab.external_lab_dto import ExternalLabWithUserInfo
from gws_core.resource.id_mapper import IdMapper
from gws_core.resource.resource import Resource
from gws_core.resource.resource_dto import ResourceModelExportDTO, ResourceOrigin
from gws_core.resource.resource_loader import ResourceLoader
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.resource_model_loader import ResourceModelLoader
from gws_core.resource.resource_set.resource_list_base import ResourceListBase
from gws_core.share.shared_dto import SharedEntityMode
from gws_core.share.shared_resource import SharedResource
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.tag import TagOrigin
from gws_core.tag.tag_entity_type import TagEntityType
from gws_core.tag.tag_list import TagList
from gws_core.user.current_user_service import CurrentUserService


class ResourceBuilder:
    """Parent class for building and persisting resources regardless of source.

    Shared state and internal helpers live here. Subclasses implement ``save()``
    for their specific source type (metadata-only DTO or full zip content).
    """

    _origin: ExternalLabWithUserInfo
    _skip_resource_tags: bool
    _message_dispatcher: MessageDispatcher | None
    _id_mapper: IdMapper

    _loaded_resource: Resource | None
    _children_resources: dict[str, Resource]
    _children_resource_models: list[ResourceModel]

    def __init__(
        self,
        origin: ExternalLabWithUserInfo,
        id_mapper: IdMapper,
        skip_resource_tags: bool = False,
        message_dispatcher: MessageDispatcher | None = None,
    ):
        self._origin = origin
        self._id_mapper = id_mapper
        self._skip_resource_tags = skip_resource_tags
        self._message_dispatcher = message_dispatcher
        self._loaded_resource = None
        self._children_resources = {}
        self._children_resource_models = []

    # ------------------------------------------------------------------
    # Abstract
    # ------------------------------------------------------------------

    @abstractmethod
    def save(self) -> ResourceModel:
        """Save the resource to the DB. Each subclass implements its own logic."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_loaded_resource(self) -> Resource | None:
        """Return the loaded resource, available after ``save()`` has been called."""
        return self._loaded_resource

    def get_children_resources(self) -> dict[str, Resource]:
        """Return the children resources, available after ``save()`` has been called."""
        return self._children_resources

    def get_children_resource_models(self) -> list[ResourceModel]:
        """Return the children resource models, available after ``save()`` has been called."""
        return self._children_resource_models

    def cleanup(self) -> None:
        """Clean up temporary files. No-op in base class."""

    # ------------------------------------------------------------------
    # Internal helpers (shared logic)
    # ------------------------------------------------------------------

    def _resolve_id(self, old_resource_id: str) -> str:
        """Resolve an old resource ID to the actual DB ID.

        In NEW_ID mode, returns the mapped new ID. In KEEP_ID mode, returns the same ID.
        """
        return self._id_mapper.generate_new_id(old_resource_id)


class ResourceDtoBuilder(ResourceBuilder):
    """Handles metadata-only resources (no zip content).

    Creates or resolves a resource model shell in the DB from a ``ResourceModelExportDTO``.
    """

    _resource_model_dto: ResourceModelExportDTO

    def __init__(
        self,
        resource_model_dto: ResourceModelExportDTO,
        origin: ExternalLabWithUserInfo,
        id_mapper: IdMapper,
        skip_resource_tags: bool = False,
        message_dispatcher: MessageDispatcher | None = None,
    ):
        super().__init__(origin, id_mapper, skip_resource_tags, message_dispatcher)
        self._resource_model_dto = resource_model_dto

    def save(self) -> ResourceModel:
        """Save a shell resource model from DTO metadata.

        KEEP_ID mode:
        - Doesn't exist: create shell (content_is_deleted=True), save it
        - Exists: update attributes from DTO, save it

        NEW_ID mode:
        - Always create a new shell with a fresh UUID
        """
        return self._resolve_or_create_resource_model(self._resource_model_dto)

    def get_resource_model_dto(self) -> ResourceModelExportDTO:
        return self._resource_model_dto

    def _resolve_or_create_resource_model(
        self,
        dto: ResourceModelExportDTO,
    ) -> ResourceModel:
        """Resolve an existing ResourceModel from the DB or create a new shell from metadata."""

        resource_model_id = self._resolve_id(dto.id)
        resource_model = ResourceModel.get_by_id(resource_model_id)

        resource_model_loader = ResourceModelLoader(dto, self._id_mapper, self._message_dispatcher)

        if resource_model is None:
            # Create a new shell from metadata
            resource_model = resource_model_loader.load_resource_model(
                origin=ResourceOrigin.IMPORTED_FROM_LAB,
            )
        else:
            # Resource exists — update attributes from DTO
            resource_model = resource_model_loader.update_resource_model(
                resource_model,
                origin=ResourceOrigin.IMPORTED_FROM_LAB,
            )

        resource_model.id = self._resolve_id(dto.id)
        resource_model.parent_resource_id = (
            self._resolve_id(dto.parent_resource_id) if dto.parent_resource_id else None
        )

        return resource_model.save_full()


class ResourceZipBuilder(ResourceBuilder):
    """Handles full zip imports with content via a pre-loaded ``ResourceLoader``.

    The caller is responsible for creating the ``ResourceLoader``
    (e.g. via ``ResourceLoader.from_compress_file()``).
    """

    _resource_loader: ResourceLoader

    def __init__(
        self,
        resource_loader: ResourceLoader,
        origin: ExternalLabWithUserInfo,
        id_mapper: IdMapper,
        skip_resource_tags: bool = False,
        message_dispatcher: MessageDispatcher | None = None,
    ):
        super().__init__(origin, id_mapper, skip_resource_tags, message_dispatcher)
        self._resource_loader = resource_loader

    def save(self) -> ResourceModel:
        """Save the resource with its full content directly.

        KEEP_ID mode:
        - Doesn't exist: create and save with content
        - Exists without content (content_is_deleted=True): fill the content
        - Exists with content: return as-is

        NEW_ID mode:
        - Always create a new resource with a fresh UUID and save with content

        Also handles children resources (for ResourceListBase) and
        creates SharedResource provenance records.
        """
        main_resource_dto = self._resource_loader.get_main_resource()
        main_resource = self._resource_loader.load_resource()
        generated_children = self._resource_loader.get_generated_children_resources()

        # store the generated children by parent so we set the parent_id after
        children_resource_models: list[ResourceModel] = []

        # Save children first if this is a ResourceListBase
        if len(generated_children) > 0 and isinstance(main_resource, ResourceListBase):
            new_children_resources: dict[str, Resource] = {}

            for child_old_id, child_resource in generated_children.items():
                    child_dto = self._resource_loader.get_children_dto(child_old_id)
                    if child_dto is None:
                        raise Exception(
                            f"Missing DTO metadata for child resource with old id '{child_old_id}'"
                        )
                    child_model = self._save_resource(
                        child_old_id,
                        child_resource,
                        resource_model_export_dto=child_dto.resource_model_export,
                    )
                    new_children_resources[child_resource.uid] = child_model.get_resource()
                    self._children_resource_models.append(child_model)

                    # Store the children that were generated by parent to link them later
                    if (
                        child_dto.resource_model_export.parent_resource_id
                        == main_resource_dto.resource_model_export.id
                    ):
                        children_resource_models.append(child_model)
            main_resource.__set_r_field__(new_children_resources)

        # Store the loaded resource and children
        self._loaded_resource = main_resource
        self._children_resources = generated_children

        # Save the main resource
        resource_model = self._save_resource(
            self._resource_loader.get_main_resource_origin_id(),
            main_resource,
            resource_model_export_dto=main_resource_dto.resource_model_export,
        )

        # Set parent on owned children
        for child_model in children_resource_models:
            child_model.set_parent_and_save(resource_model.id)

        return resource_model

    def _save_resource(
        self,
        old_resource_id: str,
        resource: Resource,
        resource_model_export_dto: ResourceModelExportDTO | None = None,
    ) -> ResourceModel:
        """Save a single resource directly with its content.

        In KEEP_ID mode, checks for an existing model:
        - If it exists with content, update model data
        - If it exists with content_is_deleted, fills the content.
        - If it doesn't exist, creates a new model with content.

        In NEW_ID mode, creates a new model with a fresh UUID.
        """
        resolved_id = self._resolve_id(old_resource_id)

        resource_model = ResourceModel.get_by_id(resolved_id)

        try:
            if resource_model and resource_model.content_is_deleted:
                resource_model = resource_model.fill_content_from_resource(resource)

                # fill_content_from_resource doesn't save tags, do it here
                if resource.tags and isinstance(resource.tags, TagList):
                    user_origin = TagOrigin.current_user_origin()
                    entity_tags = EntityTagList(
                        TagEntityType.RESOURCE, resource_model.id, default_origin=user_origin
                    )
                    entity_tags.add_tags(resource.tags.get_tags())
            if not resource_model:
                resource_model = ResourceModel.save_from_resource(
                    resource,
                    origin=ResourceOrigin.IMPORTED_FROM_LAB,
                    skip_children=True,
                    id=resolved_id,
                )

        except Exception as err:
            raise Exception(
                f"Error while saving resource with old id '{old_resource_id}'. {str(err)}"
            ) from err

        # Update the resource_model information (like scenario, task, project...)
        if resource_model_export_dto is not None:
            ResourceModelLoader(
                resource_model_export_dto, self._id_mapper, self._message_dispatcher
            ).update_resource_model(
                resource_model,
                origin=ResourceOrigin.IMPORTED_FROM_LAB,
            )
            resource_model.save()

        SharedResource.create_from_lab_info(
            resource_model.id,
            SharedEntityMode.RECEIVED,
            self._origin,
            CurrentUserService.get_and_check_current_user(),
            external_id=old_resource_id,
        )

        return resource_model

    def cleanup(self) -> None:
        """Delete temporary resource folder created during zip extraction."""
        self._resource_loader.delete_resource_folder()

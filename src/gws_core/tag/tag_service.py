from collections.abc import Callable
from typing import Any

from peewee import ModelSelect

from gws_core.community.community_dto import CommunityTagKeyDTO, CommunityTagValueDTO
from gws_core.community.community_service import CommunityService
from gws_core.config.param.param_types import ParamSpecSimpleDTO
from gws_core.core.classes.paginator import Paginator
from gws_core.core.classes.search_builder import SearchParams
from gws_core.core.db.gws_core_db_manager import GwsCoreDbManager
from gws_core.core.model.model import Model
from gws_core.core.model.model_dto import PageDTO
from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.string_helper import StringHelper
from gws_core.entity_navigator.entity_navigator import EntityNavigator
from gws_core.entity_navigator.entity_navigator_deep import NavigableEntitySet
from gws_core.entity_navigator.entity_navigator_type import NavigableEntityType
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.view_config.view_config import ViewConfig
from gws_core.scenario.scenario import Scenario
from gws_core.tag.entity_tag import EntityTag
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.entity_with_tag_search_builder import EntityWithTagSearchBuilder
from gws_core.tag.tag_dto import (
    NewTagDTO,
    ShareTagMode,
    TagKeyModelDTO,
    TagKeyNotSynchronizedFields,
    TagNotSynchronizedDTO,
    TagOriginDetailDTO,
    TagOriginType,
    TagPropagationImpactDTO,
    TagsNotSynchronizedDTO,
    TagValueEditDTO,
    TagValueModelDTO,
    TagValueNotSynchronizedFields,
    TagValueNotSynchronizedFieldsDTO,
)
from gws_core.tag.tag_entity_type import TagEntityType
from gws_core.tag.tag_search_builder import TagSearchBuilder
from gws_core.tag.tag_value_model import TagValueModel
from gws_core.task.task_model import TaskModel
from gws_core.user.current_user_service import CurrentUserService
from gws_core.user.user import User

from ..core.exception.exceptions.bad_request_exception import BadRequestException
from .tag import Tag, TagOrigin, TagValueType
from .tag_key_model import TagKeyModel


class TagService:
    @classmethod
    def get_all_tags(cls) -> list[TagKeyModel]:
        return TagKeyModel.get_all_ordered_by_order()

    @classmethod
    def search(
        cls, search: SearchParams, page: int = 0, number_of_items_per_page: int = 20
    ) -> Paginator[TagKeyModel]:
        search_builder = TagSearchBuilder()

        return search_builder.add_search_params(search).search_page(page, number_of_items_per_page)

    @classmethod
    def search_keys(
        cls, tag_key: str | None, page: int = 0, number_of_items_per_page: int = 20
    ) -> PageDTO[TagKeyModelDTO]:
        if tag_key:
            model_select: ModelSelect = TagKeyModel.search_by_key(tag_key)
        else:
            model_select: ModelSelect = TagKeyModel.get_all_ordered_by_key()

        paginator = Paginator(
            model_select, page=page, nb_of_items_per_page=number_of_items_per_page
        )

        return paginator.to_dto()

    @classmethod
    def search_values(
        cls, tag_key: str, tag_value: str | None, page: int = 0, number_of_items_per_page: int = 20
    ) -> Paginator[TagValueModel]:
        model_select: ModelSelect = TagValueModel.search_by_value(tag_key, tag_value)
        return Paginator(model_select, page=page, nb_of_items_per_page=number_of_items_per_page)

    @classmethod
    def get_tag_key_model(cls, tag_key: str) -> TagKeyModel | None:
        return TagKeyModel.get_by_key(tag_key)

    @classmethod
    @GwsCoreDbManager.transaction()
    def update_registered_tag_value(
        cls, tag_key: str, old_value: TagValueType, new_value: TagValueType
    ) -> TagValueModel:
        """Update a registerer tag value. It update the tag of all entities that use it"""

        tag_key_model = TagKeyModel.get_and_check_by_key(tag_key)

        if not TagValueModel.tag_value_exists(tag_key_model, old_value):
            raise BadRequestException(
                f"The tag with key '{tag_key}' and value '{old_value}' does not exists"
            )

        # update the TagModel
        return TagValueModel.update_tag_value(tag_key, old_value, new_value)

    @classmethod
    @GwsCoreDbManager.transaction()
    def delete_tag_key(cls, key: str) -> None:
        """Delete a registerer tag key. It removes the tag of all entities that use it"""
        tag_key_model = TagKeyModel.get_and_check_by_key(key)

        tag_values: list[TagValueModel] = TagValueModel.get_by_tag_key(tag_key_model)

        for tag_value in tag_values:
            TagValueModel.delete_instance(tag_value)

        # delete the tag key
        TagKeyModel.delete_instance(tag_key_model)

    @classmethod
    @GwsCoreDbManager.transaction()
    def delete_tag_value(cls, tag_value_id: str) -> None:
        """Delete a registerer tag value. It removes the tag of all entities that use it"""
        tag_value = TagValueModel.get_tag_value_model_by_id(tag_value_id)

        if not tag_value:
            raise BadRequestException(f"The tag value with id '{tag_value_id}' does not exists")

        if tag_value.is_community_tag_value:
            raise BadRequestException(
                f"The tag value with id '{tag_value_id}' is a community tag value and cannot be deleted."
            )

        TagValueModel.delete_instance(tag_value)

    @classmethod
    @GwsCoreDbManager.transaction()
    def delete_registered_tag(cls, tag_key: str, tag_value: TagValueType) -> None:
        """Update a registerer tag value. It removes the tag of all entities that use it"""
        tag_key_model = TagKeyModel.get_and_check_by_key(tag_key)

        if not TagValueModel.tag_value_exists(tag_key_model, tag_value):
            raise BadRequestException(
                f"The tag with key '{tag_key}' and value '{tag_value}' does not exists"
            )

        TagValueModel.delete_tag_value(tag_key, tag_value)

    @classmethod
    @GwsCoreDbManager.transaction()
    def reorder_tags(cls, tag_keys: list[str]) -> list[TagKeyModel]:
        """Update the order of the tags"""

        tag_models: list[TagKeyModel] = cls.get_all_tags()

        result: list[TagKeyModel] = []
        for i, key in enumerate(tag_keys):
            tag_model_filtererd: list[TagKeyModel] = [x for x in tag_models if x.key == key]

            if len(tag_model_filtererd) == 0:
                continue

            tag_model = tag_model_filtererd[0]
            tag_model.order = i
            tag_model.save()
            result.append(tag_model)

        return result

    @classmethod
    @GwsCoreDbManager.transaction()
    def create_tag(cls, tag_key: str, tag_value: TagValueType) -> TagValueModel:
        """Create a new tag with the given key and value"""
        tag_key_model = TagKeyModel.get_by_key(tag_key)
        if not tag_key_model:
            tag_key_model = cls.create_tag_key(
                tag_key, StringHelper.camel_case_to_sentence(tag_key)
            )

        if TagValueModel.tag_value_exists(tag_key_model, tag_value):
            raise BadRequestException(
                f"The tag value '{tag_value}' already exists for the key '{tag_key}'."
            )

        tag_value_model: TagValueModel = cls.create_tag_value(
            edit_tag_value=TagValueEditDTO(
                id=None,
                value=tag_value,
                short_description=None,
                additional_infos=None,
                tag_key=tag_key_model.key,
            ),
            tag_key_model=tag_key_model,
        )
        return tag_value_model.save()

    @classmethod
    def create_tag_key(cls, key: str, label: str) -> TagKeyModel:
        if TagKeyModel.get_by_key(key):
            raise ValueError(f"The tag key '{key}' already exists. Please use a different key.")

        Tag.validate_tag(key)

        # create the tag key model
        tag_key_model = TagKeyModel.create_tag_key_model(key=key, label=label)
        return tag_key_model.save()

    @classmethod
    def create_tag_value(
        cls, edit_tag_value: TagValueEditDTO, tag_key_model: TagKeyModel | None = None
    ) -> TagValueModel:
        """Create a new tag value"""
        if not tag_key_model:
            tag_key_model = TagKeyModel.get_by_key(edit_tag_value.tag_key)

        if not tag_key_model:
            raise ValueError(
                f"The tag key '{edit_tag_value.tag_key}' does not exists. Please create it first."
            )

        if TagValueModel.get_tag_value_model_by_key_and_value(
            edit_tag_value.tag_key, edit_tag_value.value
        ):
            raise ValueError(
                f"The tag value '{edit_tag_value.value}' already exists for the key '{edit_tag_value.tag_key}'."
            )

        # create the tag value model
        return TagValueModel.create_tag_value_model(
            tag_key_model=tag_key_model,
            tag_value=edit_tag_value.value,
            short_description=edit_tag_value.short_description,
            additional_infos=edit_tag_value.additional_infos,
        )

    @classmethod
    def update_tag_value(cls, key: str, edit_tag_value: TagValueEditDTO) -> TagValueModel:
        """Update a tag value"""
        tag_value_model = TagValueModel.get_tag_value_model_by_key_and_value(
            key, edit_tag_value.value
        )

        if not tag_value_model:
            raise BadRequestException(
                f"The tag value '{edit_tag_value.value}' does not exists for the key '{key}'."
            )

        if edit_tag_value.short_description is not None:
            tag_value_model.short_description = edit_tag_value.short_description
        if edit_tag_value.additional_infos is not None:
            tag_value_model.additional_infos = edit_tag_value.additional_infos

        return tag_value_model.save()

    ################################# TAGGABLE MODEL #################################

    @classmethod
    def get_entities_by_tag(cls, entity_type: TagEntityType, tag: Tag) -> list[Model]:
        search_builder = EntityWithTagSearchBuilder(
            entity_type.get_entity_model_type(), entity_type
        )

        return search_builder.add_tag_filter(tag).search_all()

    @classmethod
    @GwsCoreDbManager.transaction()
    def add_tag_to_entity(cls, entity_type: TagEntityType, entity_id: str, tag: Tag) -> EntityTag:
        # add tag to the list of tags
        entity_tags = EntityTagList.find_by_entity(entity_type, entity_id)

        if not tag.origin_is_defined():
            tag.origins.add_origin(
                TagOrigin(TagOriginType.USER, CurrentUserService.get_and_check_current_user().id)
            )

        return entity_tags.add_tag(tag)

    @classmethod
    @GwsCoreDbManager.transaction()
    def add_tags_to_entity(
        cls, entity_type: TagEntityType, entity_id: str, tags: list[Tag]
    ) -> list[EntityTag]:
        entity_tags = EntityTagList.find_by_entity(entity_type, entity_id)

        for tag in tags:
            if not tag.origin_is_defined():
                tag.origins.add_origin(
                    TagOrigin(
                        TagOriginType.USER, CurrentUserService.get_and_check_current_user().id
                    )
                )

        return entity_tags.add_tags(tags)

    @classmethod
    @GwsCoreDbManager.transaction()
    def add_tag_dict_to_entity(
        cls, entity_type: TagEntityType, entity_id: str, tag_dicts: list[NewTagDTO], propagate: bool
    ) -> list[EntityTag]:
        tags = cls._build_tags_from_dicts(tag_dicts, propagate)

        if propagate:
            return cls.add_tags_to_entity_and_propagate(entity_type, entity_id, tags)
        else:
            return cls.add_tags_to_entity(entity_type, entity_id, tags)

    @classmethod
    @GwsCoreDbManager.transaction()
    def add_tag_dict_to_entities(
        cls,
        entity_type: TagEntityType,
        entity_ids: list[str],
        tag_dicts: list[NewTagDTO],
        propagate: bool,
    ) -> dict[str, list[EntityTag]]:
        """Add the given tags to several entities of the same type.

        Returns a dict mapping each entity id to the tags added to it."""
        # the tags (and their community keys) only need to be built/registered once
        tags = cls._build_tags_from_dicts(tag_dicts, propagate)

        result: dict[str, list[EntityTag]] = {}
        for entity_id in entity_ids:
            if propagate:
                result[entity_id] = cls.add_tags_to_entity_and_propagate(
                    entity_type, entity_id, tags
                )
            else:
                result[entity_id] = cls.add_tags_to_entity(entity_type, entity_id, tags)

        return result

    @classmethod
    def _build_tags_from_dicts(cls, tag_dicts: list[NewTagDTO], propagate: bool) -> list[Tag]:
        """Build Tag objects from the DTOs, registering their community tag keys if needed"""
        tags = [
            Tag(
                key=tag_dict.key,
                value=tag_dict.value,
                is_propagable=propagate,
                is_community_tag_key=tag_dict.is_community_tag_key,
                is_community_tag_value=tag_dict.is_community_tag_value,
                additional_info=tag_dict.additional_info,
                auto_parse=True,
            )
            for tag_dict in tag_dicts
        ]

        for tag in tags:
            cls._register_community_tag_key(tag)

        return tags

    @classmethod
    def _register_community_tag_key(cls, tag: Tag) -> None:
        """Import the community tag key (and its values) for the tag if not already registered"""
        if not tag.is_community_tag_key:
            return

        # check if community tag is already registered
        current_tag_key = TagKeyModel.get_by_key(tag.key)
        if not current_tag_key:
            # get Community Tag Key and create it if not exists
            community_tag_key = CommunityService.get_community_tag_key(tag.key)
            if not community_tag_key:
                raise BadRequestException(
                    f"The community tag key '{tag.key}' does not exists. Please create it first."
                )

            tag_key = TagKeyModel.from_community_tag_key(community_tag_key)
            if tag_key:
                tag_key = tag_key.save()
                cls.import_all_community_tag_key_values(tag_key)
        elif tag.is_community_tag_value:
            cls.import_all_community_tag_key_values(current_tag_key)

    @classmethod
    @GwsCoreDbManager.transaction()
    def add_tags_to_entity_and_propagate(
        cls, entity_type: TagEntityType, entity_id: str, tags: list[Tag]
    ) -> list[EntityTag]:
        entity_tags = cls.add_tags_to_entity(entity_type, entity_id, tags)

        # propagate the tag to the next entities
        entity_nav = EntityNavigator.from_entity_id(
            entity_type.convert_to_navigable_entity_type(), entity_id
        )
        entity_nav.propagate_tags(tags)

        return entity_tags

    @classmethod
    def find_by_entity_id(cls, entity_type: TagEntityType, entity_id: str) -> EntityTagList:
        return EntityTagList.find_by_entity(entity_type, entity_id)

    @classmethod
    def delete_tag_from_entity(
        cls, entity_type: TagEntityType, entity_id: str, tag_key: str, tag_value: TagValueType
    ) -> None:
        entity_tags = EntityTagList.find_by_entity(entity_type, entity_id)

        tag_to_delete = Tag(tag_key, tag_value)
        current_tag = entity_tags.get_tag(tag_to_delete)

        if not current_tag:
            return

        if not current_tag.origin_is_user():
            raise BadRequestException("You can't delete a tag that is not created by a user")

        current_tag = entity_tags.get_tag(tag_to_delete)

        if current_tag:
            entity_tags.delete_tag(tag_to_delete)

            if current_tag.is_propagable:
                entity_nav = EntityNavigator.from_entity_id(
                    entity_type.convert_to_navigable_entity_type(), entity_id
                )
                entity_nav.delete_propagated_tags([tag_to_delete])

    @classmethod
    def check_propagation_add_tags(
        cls, entity_type: TagEntityType, entity_ids: list[str], tags: list[NewTagDTO]
    ) -> TagPropagationImpactDTO:
        """Check the impact of the propagation of the given tags on the given entities"""
        new_tags: list[Tag] = [
            Tag(
                key=tag.key,
                value=tag.value,
                is_community_tag_key=tag.is_community_tag_key,
                is_community_tag_value=tag.is_community_tag_value,
                additional_info=tag.additional_info,
                auto_parse=True,
            )
            for tag in tags
        ]

        return cls._check_tag_propagation_impact(entity_type, entity_ids, new_tags)

    @classmethod
    def check_propagation_delete_tag(
        cls, entity_type: TagEntityType, entity_ids: list[str], tag: NewTagDTO
    ) -> TagPropagationImpactDTO:
        """Check the impact of the deletion of the given tag on the given entities"""

        tag_to_delete = Tag(tag.key, tag.value)

        # entities for which the tag is propagable: their downstream entities are impacted
        propagable_entity_ids: list[str] = []
        # entities for which the tag exists but is not propagable: only themselves are impacted
        non_propagable_entity_ids: list[str] = []

        for entity_id in entity_ids:
            entity_tags = EntityTagList.find_by_entity(entity_type, entity_id)
            existing_tag = entity_tags.get_tag(tag_to_delete)

            if not existing_tag:
                continue

            if existing_tag.is_propagable:
                propagable_entity_ids.append(entity_id)
            else:
                non_propagable_entity_ids.append(entity_id)

        if not propagable_entity_ids and not non_propagable_entity_ids:
            raise BadRequestException("The tag does not exists for any of the objects")

        navigable_entity_type = entity_type.convert_to_navigable_entity_type()

        impacted_entities = NavigableEntitySet()

        # downstream entities of the propagable occurrences
        if propagable_entity_ids:
            entity_nav = EntityNavigator.from_entity_ids(
                navigable_entity_type, propagable_entity_ids
            )
            impacted_entities.update(
                cls._get_propagation_impacted_entities(entity_nav).get_entities()
            )

        # non-propagable occurrences only impact themselves
        if non_propagable_entity_ids:
            entity_nav = EntityNavigator.from_entity_ids(
                navigable_entity_type, non_propagable_entity_ids
            )
            impacted_entities.update(entity_nav.get_as_nav_set().get_entities())

        return TagPropagationImpactDTO(
            tags=[tag_to_delete.to_dto()],
            impacted_entities=impacted_entities.get_entity_dict_nav_group(),
        )

    @classmethod
    def _check_tag_propagation_impact(
        cls, entity_type: TagEntityType, entity_ids: list[str], tags: list[Tag]
    ) -> TagPropagationImpactDTO:
        """Check the impact of the propagation of the given tags on the given entities"""
        entity_nav = EntityNavigator.from_entity_ids(
            entity_type.convert_to_navigable_entity_type(), entity_ids
        )
        next_entities = cls._get_propagation_impacted_entities(entity_nav)

        return TagPropagationImpactDTO(
            tags=[tag.to_dto() for tag in tags],
            impacted_entities=next_entities.get_entity_dict_nav_group(),
        )

    @classmethod
    def _get_propagation_impacted_entities(
        cls, entity_nav: EntityNavigator
    ) -> NavigableEntitySet:
        """Return the entities impacted by a tag propagation (the entities and their descendants).

        Tags can't be propagated to SCENARIO."""
        return entity_nav.get_next_entities_recursive(
            [NavigableEntityType.RESOURCE, NavigableEntityType.VIEW, NavigableEntityType.NOTE],
            include_current_entities=True,
        )

    @classmethod
    def get_and_check_entity_tag(cls, entity_tag_id: str) -> EntityTag:
        return EntityTag.get_by_id_and_check(entity_tag_id)

    @classmethod
    def get_tag_origins(cls, entity_tag_id: str) -> list[TagOriginDetailDTO]:
        entity_tag = cls.get_and_check_entity_tag(entity_tag_id)

        origins: list[TagOriginDetailDTO] = []

        for origin in entity_tag.get_origins().get_origins():
            origins.append(cls._get_tag_origin_detail(origin))

        return origins

    @classmethod
    def _get_tag_origin_detail(cls, tag_origin: TagOrigin) -> TagOriginDetailDTO:
        origin_detail = TagOriginDetailDTO(
            origin_type=tag_origin.origin_type, origin_id=tag_origin.origin_id, origin_object=None
        )
        origin_detail.origin_object = cls._resolve_tag_origin_object(tag_origin)
        return origin_detail

    @classmethod
    def _resolve_tag_origin_object(cls, tag_origin: TagOrigin) -> Any:
        """Resolve the object referenced by a tag origin (user dto, task/scenario/... name)"""
        origin_id = tag_origin.origin_id

        if tag_origin.origin_type == TagOriginType.USER:
            user = User.get_by_id(origin_id)
            return user.to_dto() if user else None
        if tag_origin.origin_type in (TagOriginType.TASK, TagOriginType.TASK_PROPAGATED):
            task_model = TaskModel.get_by_id_and_check(origin_id)
            return task_model.name if task_model else None
        if tag_origin.origin_type == TagOriginType.SCENARIO_PROPAGATED:
            scenario = Scenario.get_by_id(origin_id)
            return scenario.title if scenario else None
        if tag_origin.origin_type == TagOriginType.RESOURCE_PROPAGATED:
            resource = ResourceModel.get_by_id(origin_id)
            return resource.name if resource else None
        if tag_origin.origin_type == TagOriginType.VIEW_PROPAGATED:
            view = ViewConfig.get_by_id(origin_id)
            return view.title if view else None

        return None

    ################################### COMMUNITY TAG #################################

    @classmethod
    def get_tag_value_by_key_and_value(
        cls, tag_key: str, tag_value: TagValueType
    ) -> TagValueModel | None:
        """Get the community tag value by key and value"""
        return TagValueModel.get_tag_value_model_by_key_and_value(tag_key, tag_value)

    @classmethod
    def share_tag_to_community(
        cls, tag_key: str, publish_mode: ShareTagMode, space_selected: str | None = None
    ) -> TagKeyModel:
        """Share a tag to the community"""
        tag_key_model: TagKeyModel = TagKeyModel.get_and_check_by_key(tag_key)

        if tag_key_model.is_community_tag:
            raise BadRequestException(
                f"The tag key '{tag_key}' is already shared to the community."
            )

        new_community_tag_key: CommunityTagKeyDTO = tag_key_model.to_community_dto()

        new_community_tag_values = cls.get_new_community_tag_values(tag_key_model)

        # share the tag key to the community
        shared_community_tag = CommunityService.share_tag_to_community(
            new_community_tag_key, new_community_tag_values, publish_mode, space_selected
        )

        if not shared_community_tag:
            raise BadRequestException(
                f"Error while sharing the tag key '{tag_key}' to the community."
            )

        # # update the tag key model
        tag_key_model.is_community_tag = True
        tag_key_model.key = shared_community_tag.key

        return tag_key_model.save()

    @classmethod
    def _fetch_community_page(
        cls, error_message: str, fetch: Callable[[], PageDTO]
    ) -> PageDTO | None:
        """Run a community page fetch, logging and returning None on error"""
        try:
            return fetch()
        except Exception as e:
            Logger.error(f"{error_message}: {e}")
            return None

    @classmethod
    @GwsCoreDbManager.transaction()
    def get_community_available_tags(
        cls,
        spaces_filter: list[str],
        title_filter: str,
        personal_only: bool,
        page: int,
        number_of_items_per_page: int,
    ) -> PageDTO[TagKeyModelDTO]:
        """Get the community available tags"""
        community_tags_keys = cls._fetch_community_page(
            "Error while getting community available tags",
            lambda: CommunityService.get_available_community_tags(
                spaces_filter, "", title_filter, personal_only, page, number_of_items_per_page
            ),
        )
        if community_tags_keys is None:
            return PageDTO.empty_page()
        return cls.community_tag_key_page_to_tag_key_model_page(community_tags_keys)

    @classmethod
    @GwsCoreDbManager.transaction()
    def get_community_tag_values(
        cls, community_tag_key: str, page: int, number_of_items_per_page: int
    ) -> PageDTO[TagValueModelDTO]:
        """Get the community tags"""
        community_tags = cls._fetch_community_page(
            "Error while getting community tag values",
            lambda: CommunityService.get_community_tag_values(
                community_tag_key, page=page, number_of_items_per_page=number_of_items_per_page
            ),
        )
        if community_tags is None:
            return PageDTO.empty_page()

        # keep only the community values that are not yet imported in the system
        objects: list[TagValueModelDTO] = [
            cls._community_tag_value_to_dto(tag_value)
            for tag_value in community_tags.objects
            if not TagValueModel.get_tag_value_model_by_id(tag_value.id)
        ]

        return community_tags.with_objects(objects)

    @classmethod
    def _community_tag_value_to_dto(
        cls, community_tag_value: CommunityTagValueDTO
    ) -> TagValueModelDTO:
        """Build a (not yet persisted) tag value DTO from a community tag value"""
        return TagValueModelDTO(
            id=community_tag_value.id,
            created_at=DateHelper.now_utc(),
            last_modified_at=DateHelper.now_utc(),
            value=community_tag_value.value,
            key=community_tag_value.tag_key.key,
            value_format=community_tag_value.tag_key.value_format,
            is_community_tag_value=True,
            deprecated=community_tag_value.deprecated,
            short_description=community_tag_value.short_description,
            additional_infos=community_tag_value.additional_infos,
        )

    @classmethod
    def get_new_community_tag_values(cls, tag_key: TagKeyModel) -> list[CommunityTagValueDTO]:
        """Get the new community tag values for a tag key"""
        values: list[TagValueModel] = TagValueModel.get_non_community_values_by_tag_key(tag_key)
        return [value.to_community_dto() for value in values]

    @classmethod
    def search_community_tag_keys_by_key(
        cls, tag_key: str, number_of_items_per_page: int, page: int
    ) -> PageDTO[TagKeyModelDTO]:
        """Get the community tags by key"""
        community_tags_keys = cls._fetch_community_page(
            "Error while searching community tag keys",
            lambda: CommunityService.get_available_community_tags(
                key_filter=tag_key,
                label_filter=None,
                number_of_items_per_page=number_of_items_per_page,
                page=page,
                spaces_filter=[],
                personal_only=False,
            ),
        )
        if community_tags_keys is None:
            return PageDTO.empty_page()

        return cls.community_tag_key_page_to_tag_key_model_page(community_tags_keys)

    @classmethod
    def community_tag_key_page_to_tag_key_model_page(
        cls, community_tag_key_page: PageDTO[CommunityTagKeyDTO]
    ) -> PageDTO[TagKeyModelDTO]:
        """Convert a community tag key page to a tag key model page"""

        objects: list[TagKeyModelDTO] = []
        for tag in community_tag_key_page.objects:
            tag_key_model = TagKeyModel.from_community_tag_key(tag)
            if not tag_key_model or TagKeyModel.get_by_key(tag_key_model.key):
                # If the tag key already exists in the system, we don't create a new one
                continue
            objects.append(tag_key_model.to_dto())

        return community_tag_key_page.with_objects(objects)

    @classmethod
    def get_not_synchronized_community_tags(cls) -> TagsNotSynchronizedDTO:
        """Get the tags that are not synchronized with the community"""

        tag_keys_not_synched: list[TagNotSynchronizedDTO] = []

        imported_community_tag_keys: list[TagKeyModel] = (
            TagKeyModel.get_community_tag_keys_imported()
        )

        for imported_community_tag_key in imported_community_tag_keys:
            current_community_tag_key_dto = CommunityService.get_community_tag_key(
                imported_community_tag_key.key
            )
            current_community_tag_key = (
                TagKeyModel.from_community_tag_key(current_community_tag_key_dto, new_only=True)
                if current_community_tag_key_dto
                else None
            )

            if not current_community_tag_key:
                Logger.info(
                    f"Community tag key '{imported_community_tag_key.key}' not found in community."
                )
                continue

            tag_key_not_sync_fields = cls._diff_tag_key_fields(
                imported_community_tag_key, current_community_tag_key
            )
            not_sync_values = cls._diff_community_tag_values(imported_community_tag_key)

            if len(tag_key_not_sync_fields) > 0 or len(not_sync_values) > 0:
                tag_keys_not_synched.append(
                    TagNotSynchronizedDTO(
                        old_key=imported_community_tag_key.to_dto(),
                        new_key=current_community_tag_key.to_dto(),
                        not_synchronized_fields=tag_key_not_sync_fields,
                        not_synchronized_values=not_sync_values,
                    )
                )

        return TagsNotSynchronizedDTO(tag_keys_not_synchronized=tag_keys_not_synched)

    @classmethod
    def _diff_tag_key_fields(
        cls, saved_key: TagKeyModel, current_key: TagKeyModel
    ) -> list[TagKeyNotSynchronizedFields]:
        """Return the tag key fields that differ between the saved and current community key"""
        not_sync_fields: list[TagKeyNotSynchronizedFields] = []
        if saved_key.label != current_key.label:
            not_sync_fields.append(TagKeyNotSynchronizedFields.LABEL)
        if saved_key.description != current_key.description:
            not_sync_fields.append(TagKeyNotSynchronizedFields.DESCRIPTION)
        if saved_key.deprecated != current_key.deprecated:
            not_sync_fields.append(TagKeyNotSynchronizedFields.DEPRECATED)
        if saved_key.additional_infos_specs != current_key.additional_infos_specs:
            not_sync_fields.append(TagKeyNotSynchronizedFields.ADDITIONAL_INFOS_SPECS)
        return not_sync_fields

    @classmethod
    def _diff_community_tag_values(
        cls, imported_community_tag_key: TagKeyModel
    ) -> list[TagValueNotSynchronizedFieldsDTO]:
        """Return the tag values that differ between the saved and current community values"""
        not_sync_values: list[TagValueNotSynchronizedFieldsDTO] = []

        current_values = CommunityService.get_all_community_tag_values(
            imported_community_tag_key.key
        )
        for current_value in current_values:
            saved_value = TagValueModel.get_tag_value_model_by_id(current_value.id)

            new_value_dto = TagValueModel.from_community_tag_value(
                current_value, tag_key=imported_community_tag_key
            ).to_dto()

            if not saved_value:
                not_sync_values.append(
                    TagValueNotSynchronizedFieldsDTO(
                        old_value=None,
                        new_value=new_value_dto,
                        not_synchronized_fields=[TagValueNotSynchronizedFields.VALUE_CREATED],
                    )
                )
                continue

            not_sync_fields: list[TagValueNotSynchronizedFields] = []
            if saved_value.short_description != current_value.short_description:
                not_sync_fields.append(TagValueNotSynchronizedFields.SHORT_DESCRIPTION)
            if saved_value.additional_infos != current_value.additional_infos:
                not_sync_fields.append(TagValueNotSynchronizedFields.ADDITIONAL_INFOS)
            if saved_value.deprecated != current_value.deprecated:
                not_sync_fields.append(TagValueNotSynchronizedFields.DEPRECATED)

            if len(not_sync_fields) > 0:
                not_sync_values.append(
                    TagValueNotSynchronizedFieldsDTO(
                        old_value=saved_value.to_dto(),
                        new_value=new_value_dto,
                        not_synchronized_fields=not_sync_fields,
                    )
                )

        return not_sync_values

    @classmethod
    def apply_sync(cls, tags_not_sync: TagsNotSynchronizedDTO) -> None:
        """Apply the synchronization of the tags with the community"""
        for tag_not_sync in tags_not_sync.tag_keys_not_synchronized:
            tag_key_model = TagKeyModel.get_and_check_by_key(tag_not_sync.old_key.key)

            cls._apply_sync_tag_key(tag_key_model, tag_not_sync)

            for not_sync_value in tag_not_sync.not_synchronized_values or []:
                cls._apply_sync_tag_value(tag_key_model, not_sync_value)

    @classmethod
    def _apply_sync_tag_key(
        cls, tag_key_model: TagKeyModel, tag_not_sync: TagNotSynchronizedDTO
    ) -> None:
        """Apply the synchronization of a single tag key fields"""
        new_key = tag_not_sync.new_key
        if not new_key or not tag_not_sync.not_synchronized_fields:
            return

        for not_sync_field in tag_not_sync.not_synchronized_fields:
            if not_sync_field == TagKeyNotSynchronizedFields.LABEL:
                tag_key_model.label = new_key.label
            elif not_sync_field == TagKeyNotSynchronizedFields.DESCRIPTION:
                tag_key_model.description = new_key.description
            elif not_sync_field == TagKeyNotSynchronizedFields.DEPRECATED:
                tag_key_model.deprecated = bool(new_key.deprecated)
                cls.deprecate_tag_values(tag_key_model)
            elif not_sync_field == TagKeyNotSynchronizedFields.ADDITIONAL_INFOS_SPECS:
                tag_key_model.additional_infos_specs = new_key.additional_infos_specs
        tag_key_model.save()

    @classmethod
    def _apply_sync_tag_value(
        cls, tag_key_model: TagKeyModel, not_sync_value: TagValueNotSynchronizedFieldsDTO
    ) -> None:
        """Apply the synchronization of a single tag value fields"""
        new_value = not_sync_value.new_value
        if not new_value or not not_sync_value.not_synchronized_fields:
            return

        if TagValueNotSynchronizedFields.VALUE_CREATED in not_sync_value.not_synchronized_fields:
            # create the tag value
            TagValueModel.from_dto(new_value, tag_key_model).save()
            return

        if not not_sync_value.old_value:
            return

        tag_value_model = TagValueModel.get_tag_value_model_by_key_and_value(
            tag_key_model.key, not_sync_value.old_value.value
        )
        if not tag_value_model:
            raise BadRequestException(
                f"The tag value '{not_sync_value.old_value.value}' does not exists "
                f"for the key '{tag_key_model.key}'."
            )

        for not_sync_field in not_sync_value.not_synchronized_fields:
            if not_sync_field == TagValueNotSynchronizedFields.SHORT_DESCRIPTION:
                tag_value_model.short_description = new_value.short_description
            elif not_sync_field == TagValueNotSynchronizedFields.ADDITIONAL_INFOS:
                tag_value_model.additional_infos = new_value.additional_infos
            elif not_sync_field == TagValueNotSynchronizedFields.DEPRECATED:
                tag_value_model.deprecated = bool(new_value.deprecated)

            tag_value_model.save()

    @classmethod
    def deprecate_tag_values(cls, tag_key_model: TagKeyModel) -> None:
        """Deprecate all tag values for a given tag key"""
        not_deprecated_tag_values: list[TagValueModel] = (
            TagValueModel.get_non_deprecated_by_tag_key(tag_key_model)
        )

        for tag_value in not_deprecated_tag_values:
            tag_value.deprecated = True
            tag_value.save()

    @classmethod
    def update_tag_key_label(cls, key: str, label: str) -> TagKeyModel:
        """Update the label of a tag key"""
        tag_key_model: TagKeyModel = TagKeyModel.get_and_check_by_key(key)

        tag_key_model.label = label
        return tag_key_model.save()

    @classmethod
    def add_additional_info_spec_to_tag_key(
        cls, key: str, spec_name: str, spec: ParamSpecSimpleDTO
    ) -> dict[str, ParamSpecSimpleDTO]:
        """Add an additional info spec to a tag key"""
        tag_key_model: TagKeyModel = TagKeyModel.get_and_check_by_key(key)

        if not tag_key_model.additional_infos_specs:
            tag_key_model.additional_infos_specs = {}

        if spec_name in tag_key_model.additional_infos_specs:
            raise BadRequestException(
                f"The additional info spec '{spec_name}' already exists for the tag key '{key}'."
            )

        tag_key_model.additional_infos_specs[spec_name] = spec.to_json_dict()

        tag_key_model = tag_key_model.save()

        return tag_key_model.additional_infos_specs or {}

    @classmethod
    def tag_has_values(cls, tag_key_model: TagKeyModel) -> bool:
        """Check if the tag key has values"""
        return TagValueModel.count_by_tag_key(tag_key_model) > 0

    @classmethod
    def update_additional_info_spec_to_tag_key(
        cls, key: str, spec_name: str, spec: ParamSpecSimpleDTO
    ) -> dict[str, ParamSpecSimpleDTO]:
        """Update an additional info spec to a tag key"""
        tag_key_model: TagKeyModel = TagKeyModel.get_and_check_by_key(key)

        if (
            not tag_key_model.additional_infos_specs
            or spec_name not in tag_key_model.additional_infos_specs
        ):
            raise BadRequestException(
                f"The additional info spec '{spec_name}' does not exists for the tag key '{key}'."
            )

        if not spec.optional and cls.tag_has_values(tag_key_model=tag_key_model):
            raise BadRequestException(
                f"The additional info spec '{spec_name}' is not optional and the tag key '{key}' has values. "
                f"Please remove the values before updating the spec or set the additional info spec to optional."
            )

        tag_key_model.additional_infos_specs[spec_name] = spec.to_json_dict()

        tag_key_model = tag_key_model.save()

        return tag_key_model.additional_infos_specs or {}

    @classmethod
    def rename_and_update_additional_info_spec_to_tag_key(
        cls, key: str, old_spec_name: str, new_spec_name: str, spec: ParamSpecSimpleDTO
    ) -> dict[str, ParamSpecSimpleDTO]:
        """Rename and update an additional info spec to a tag key"""
        tag_key_model: TagKeyModel = TagKeyModel.get_and_check_by_key(key)

        if (
            not tag_key_model.additional_infos_specs
            or old_spec_name not in tag_key_model.additional_infos_specs
        ):
            raise BadRequestException(
                f"The additional info spec '{old_spec_name}' does not exists for the tag key '{key}'."
            )

        if new_spec_name in tag_key_model.additional_infos_specs:
            raise BadRequestException(
                f"The additional info spec '{new_spec_name}' already exists for the tag key '{key}'."
            )

        # Remove the old spec and add the new one
        del tag_key_model.additional_infos_specs[old_spec_name]
        tag_key_model.additional_infos_specs[new_spec_name] = spec.to_json_dict()

        tag_key_model = tag_key_model.save()

        return tag_key_model.additional_infos_specs or {}

    @classmethod
    def delete_additional_info_spec_to_tag_key(
        cls, key: str, spec_name: str
    ) -> dict[str, ParamSpecSimpleDTO]:
        """Delete an additional info spec to a tag key"""
        tag_key_model: TagKeyModel = TagKeyModel.get_and_check_by_key(key)

        if (
            not tag_key_model.additional_infos_specs
            or spec_name not in tag_key_model.additional_infos_specs
        ):
            raise BadRequestException(
                f"The additional info spec '{spec_name}' does not exists for the tag key '{key}'."
            )

        del tag_key_model.additional_infos_specs[spec_name]

        tag_key_model = tag_key_model.save()

        return tag_key_model.additional_infos_specs or {}

    @classmethod
    @GwsCoreDbManager.transaction()
    def import_all_community_tag_key_values(cls, tag_key_model: TagKeyModel) -> None:
        """Import all community tag key values for a given key"""

        community_tag_values = CommunityService.get_all_community_tag_values(tag_key_model.key)
        for community_tag_value in community_tag_values:
            # create the tag value model for each community tag value
            if TagValueModel.get_tag_value_model_by_id(community_tag_value.id):
                # If the tag value already exists in the system, we don't create a new one
                continue
            tag_value_model = TagValueModel.from_community_tag_value(
                community_tag_value, tag_key_model
            )
            tag_value_model.save()

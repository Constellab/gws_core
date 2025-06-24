
from typing import List, Optional

from gws_core.core.decorator.transaction import transaction
from gws_core.core.utils.string_helper import StringHelper
from gws_core.entity_navigator.entity_navigator_type import EntityType
from gws_core.tag.entity_tag import EntityTag
from gws_core.tag.tag import Tag, TagOrigin
from gws_core.tag.tag_dto import EntityTagDTO, TagOriginType
from gws_core.tag.tag_key_model import TagKeyModel
from gws_core.tag.tag_value_model import TagValueModel


class EntityTagList():
    """Aggregate to manage tags of an entity
    """

    _entity_id: str
    _entity_type: EntityType

    _tags: List[EntityTag]

    _default_origin: TagOrigin = None

    def __init__(self, entity_type: EntityType, entity_id: str,
                 tags: List[EntityTag] = None,
                 default_origin: TagOrigin = None) -> None:
        self._entity_type = entity_type
        self._entity_id = entity_id

        if tags is None:
            tags = []
        self._tags = tags
        self._default_origin = default_origin

    def has_tag(self, tag: Tag) -> bool:
        """return true if the tag key and value already exist in the model
        """
        return self.get_tag(tag) is not None

    def get_tag(self, tag: Tag) -> Optional[EntityTag]:
        """return the tag if it exists
        """
        tags = [entity_tag for entity_tag in self._tags if entity_tag.tag_key ==
                tag.key and entity_tag.get_tag_value() == tag.value]

        if len(tags) > 0:
            return tags[0]

        return None

    def get_tags_by_key(self, tag_key: str) -> List[EntityTag]:
        """return the tags with the given key
        """
        return [entity_tag for entity_tag in self._tags if entity_tag.tag_key == tag_key]

    def has_tag_key(self, tag_key: str) -> bool:
        """return true if the tag key already exist in the model
        """
        return len(self.get_tags_by_key(tag_key)) > 0

    def get_tags(self) -> List[EntityTag]:
        return self._tags

    def get_tags_as_dict(self) -> dict:
        return {tag.tag_key: tag.get_tag_value() for tag in self._tags}

    def get_propagable_tags(self) -> List[EntityTag]:
        return [tag for tag in self._tags if tag.is_propagable]

    def build_tags_propagated(self, origin_type: TagOriginType, origin_id: str) -> List[Tag]:
        """Propagate the tags to the entity
        """
        return [tag.propagate_tag(origin_type, origin_id) for tag in self.get_propagable_tags()]

    def is_empty(self) -> bool:
        return len(self._tags) == 0

    @transaction()
    def add_tag(self, tag: Tag) -> EntityTag:
        """Add a tag to the list if it does not exist

        :param tag: tag to add
        :type tag: Tag
        :return: _description_
        :rtype: EntityTag
        """
        existing_tag = self.get_tag(tag)
        if existing_tag is not None:
            if self.support_multiple_origins():
                return existing_tag.merge_tag(tag)
            else:
                return existing_tag

        if not tag.origin_is_defined():
            tag.origins.add_origin(self._default_origin)

        tag_key_model = TagKeyModel.select().where(TagKeyModel.key == tag.key).first()
        tag_value_model = TagValueModel.get_tag_value_model(tag.key, tag.value)

        if tag_key_model is None:
            tag_key_model = TagKeyModel.create_tag_key_model(
                key=tag.key,
                label=StringHelper.snake_case_to_sentence(tag.key),
                value_format=tag.get_value_format(),
                is_community_tag=tag.is_community_tag_key)

        if tag_value_model is None:
            tag_value_model = TagValueModel.create_tag_value(tag_key_model=tag_key_model, tag_value=tag.value,
                                                             additional_info=tag.additional_info,
                                                             is_community_tag_value=tag.is_community_tag_value)

        new_tag = EntityTag.create_entity_tag(key=tag_key_model.key,
                                              value=tag_value_model.tag_value,
                                              is_propagable=tag.is_propagable,
                                              origins=tag.origins,
                                              value_format=tag_key_model.value_format,
                                              entity_id=self._entity_id,
                                              entity_type=self._entity_type,
                                              label=tag_key_model.label,
                                              is_community_tag=tag.is_community_tag_key)
        self._tags.append(new_tag)
        return new_tag

    @transaction()
    def add_tags(self, tags: List[Tag]) -> List[EntityTag]:
        """Add a list of tags to the list if it does not exist

        :param tags: list of tags to add
        :type tags: List[Tag]
        """

        new_tags: List[EntityTag] = []
        for tag in tags:

            # add tag to entity
            new_tags.append(self.add_tag(tag))

        return new_tags

    @transaction()
    def replace_tags(self, tags: List[Tag]) -> None:
        """Remove the tag with the same key and add the new tags
        """
        for tag in tags:
            self.replace_tag(tag)

    @transaction()
    def replace_tag(self, tag: Tag) -> None:
        """Remove the tag with the same key and add the new tag
        """
        self.delete_tag_by_key(tag.key)
        self.add_tag(tag)

    @transaction()
    def delete_tags(self, tags: List[Tag]) -> None:
        """Delete a tag from the entity tags. Check if the tag is still used by other entities
        """
        for tag in tags:
            self.delete_tag(tag)

    @transaction()
    def delete_tag(self, tag: Tag) -> None:
        """Delete a tag from the entity tags.
        If the entity support multiple origins, and the tag origin is defined, delete only the origin
        """

        # if the entity support multiple origins, delete only the origin
        if self.support_multiple_origins() and tag.origin_is_defined():
            self._delete_tag_origin(tag)
        else:
            self._delete_tag(tag)

    @transaction()
    def delete_tag_by_key(self, tag_key: str) -> None:
        """Delete a tag from the entity tags by key
        """
        tags = self.get_tags_by_key(tag_key)
        for tag in tags:
            self._delete_tag(tag.to_simple_tag())

    @transaction()
    def _delete_tag_origin(self, tag: Tag) -> None:
        """Delete a tag origin from the list, if there is no more origins, delete the tag
        """
        existing_tag = self.get_tag(tag)
        if existing_tag is None:
            return

        current_origins = existing_tag.get_origins()
        current_origins.remove_origins(tag.origins)

        # if there is not more origins, delete the tag
        if current_origins.is_empty():
            # if the tag was deleted
            self._delete_tag(tag)
        else:
            # if there is still origins, update the tag
            existing_tag.set_origins(current_origins)
            existing_tag.save()

    @transaction()
    def _delete_tag(self, tag: Tag) -> None:
        """Delete a tag from the entity tags. Check if the tag is still used by other entities
        """
        existing_tag = self.get_tag(tag)
        if existing_tag is None:
            return

        existing_tag.delete_instance()

        # check if the tag is still used by other entities
        count = EntityTag.count_by_tag(existing_tag.tag_key, existing_tag.tag_value)

        # if not, delete the tag
        if count == 0:
            TagValueModel.delete_tag_value(tag.key, tag.value)

        self._tags.remove(existing_tag)

    def to_dto(self) -> List[EntityTagDTO]:
        return [tag.to_dto() for tag in self._tags]

    def support_multiple_origins(self) -> bool:
        """Return true if the entity support multiple origins for a tag
        """
        return self._entity_type in [EntityType.NOTE]

    #################################### CLASS METHODS ####################################

    @classmethod
    def find_by_entity(cls, entity_type: EntityType, entity_id: str) -> 'EntityTagList':
        return EntityTagList(entity_type, entity_id, EntityTag.find_by_entity(entity_type, entity_id))

    @classmethod
    def delete_by_entity(cls, entity_type: EntityType, entity_id: str) -> None:
        EntityTag.delete_by_entity(entity_id, entity_type)

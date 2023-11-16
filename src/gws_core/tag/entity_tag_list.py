# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from typing import List, Optional

from gws_core.core.decorator.transaction import transaction
from gws_core.tag.entity_tag import EntityTag, EntityTagType
from gws_core.tag.tag import Tag, TagDict, TagOriginType
from gws_core.tag.tag_model import TagModel


class EntityTagList():
    """Aggregate to manage tags of an entity
    """

    _entity_id: str
    _entity_type: EntityTagType

    _tags: List[EntityTag]

    def __init__(self, entity_type: EntityTagType, entity_id: str, tags: List[EntityTag] = None) -> None:
        self._entity_type = entity_type
        self._entity_id = entity_id

        if tags is None:
            tags = []
        self._tags = tags

    def has_tag(self, tag: Tag) -> bool:
        """return true if the tag key and value already exist in the model
        """
        return self.get_tag(tag) is not None

    def get_tag(self, tag: Tag) -> Optional[EntityTag]:
        """return the tag if it exists
        """
        tags = [entity_tag for entity_tag in self._tags if entity_tag.get_tag_key() ==
                tag.key and entity_tag.get_tag_value() == tag.value]

        if len(tags) > 0:
            return tags[0]

        return None

    def get_tags(self) -> List[EntityTag]:
        return self._tags

    def get_propagable_tags(self) -> List[EntityTag]:
        return [tag for tag in self._tags if tag.is_propagable]

    @transaction()
    def add_tag_if_not_exist(self, tag: Tag) -> EntityTag:
        """Add a tag to the list if it does not exist
        """
        existing_tag = self.get_tag(tag)
        if existing_tag is not None:
            return existing_tag

         # add tag to the list of tags
        TagModel.register_tag(tag.key, tag.value)

        new_tag = EntityTag.create_entity_tag(tag, self._entity_id, self._entity_type)
        self._tags.append(new_tag)
        return new_tag

    @transaction()
    def add_tags_to_entity(self, tags: List[Tag]) -> None:

        for tag in tags:

            # add tag to entity
            self.add_tag_if_not_exist(tag)

    @transaction()
    def delete_tag(self, tag: Tag) -> None:
        """Delete a tag from the list
        """
        existing_tag = self.get_tag(tag)
        if existing_tag is None:
            return

        existing_tag.delete()

        # check if the tag is still used by other entities
        count = EntityTag.count_by_tag(existing_tag.get_tag_key(), existing_tag.get_str_tag_value())

        # if not, delete the tag
        if count == 0:
            TagModel.delete_tag(tag.key, tag.value)

        self._tags.remove(existing_tag)

    def to_json(self) -> List[TagDict]:
        return [tag.to_simple_tag().to_json() for tag in self._tags]

    #################################### CLASS METHODS ####################################

    @classmethod
    def find_by_entity(cls, entity_type: EntityTagType, entity_id: str) -> 'EntityTagList':
        return EntityTagList(entity_type, entity_id, EntityTag.find_by_entity(entity_id, entity_type))

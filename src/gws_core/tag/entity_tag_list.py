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

    def build_tags_propagated(self, origin_type: TagOriginType, origin_id: str) -> List[Tag]:
        """Propagate the tags to the entity
        """
        return [tag.propagate_tag(origin_type, origin_id) for tag in self.get_propagable_tags()]

    def is_empty(self) -> bool:
        return len(self._tags) == 0

    @transaction()
    def add_tag_if_not_exist(self, tag: Tag, update_origin: bool = False) -> EntityTag:
        """Add a tag to the list if it does not exist

        :param tag: tag to add
        :type tag: Tag
        :param update_origin: if True and the tag exist, the origin is added to the tag, defaults to False
        :type update_origin: bool, optional
        :return: _description_
        :rtype: EntityTag
        """
        existing_tag = self.get_tag(tag)
        if existing_tag is not None:
            if update_origin:
                return existing_tag.merge_tag(tag)
            else:
                return existing_tag

         # add tag to the list of tags
        tag_model = TagModel.register_tag(tag.key, tag.value)

        new_tag = EntityTag.create_entity_tag(tag, tag_model, self._entity_id, self._entity_type)
        self._tags.append(new_tag)
        return new_tag

    @transaction()
    def add_tags_to_entity(self, tags: List[Tag], update_origin: bool = False) -> None:
        """Add a list of tags to the list if it does not exist

        :param tags: list of tags to add
        :type tags: List[Tag]
        :param update_origin: if True and the tag exist, the origin is added to the tag, defaults to False
        :type update_origin: bool, optional
        """
        for tag in tags:

            # add tag to entity
            self.add_tag_if_not_exist(tag, update_origin)

    @transaction()
    def delete_tag_origins(self, tags: List[Tag]) -> None:
        """Delete a tag origin from the list
        """
        for tag in tags:
            self.delete_tag_origin(tag)

    @transaction()
    def delete_tag_origin(self, tag: Tag) -> None:
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
            self.delete_tag(tag)
        else:
            # if there is still origins, update the tag
            existing_tag.set_origins(current_origins)
            existing_tag.save()

    @transaction()
    def delete_tag(self, tag: Tag) -> None:
        """Delete a tag from the entity tags. Check if the tag is still used by other entities
        """
        existing_tag = self.get_tag(tag)
        if existing_tag is None:
            return

        existing_tag.delete_instance()

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
        return EntityTagList(entity_type, entity_id, EntityTag.find_by_entity(entity_type, entity_id))

    @classmethod
    def delete_by_entity(cls, entity_type: EntityTagType, entity_id: str) -> None:
        EntityTag.delete_by_entity(entity_id, entity_type)

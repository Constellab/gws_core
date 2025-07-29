

from typing import List, Optional

from gws_core.tag.tag import Tag, TagValueType


class TagList():

    _tags: List[Tag]

    def __init__(self, tags: List[Tag] = None) -> None:

        if tags is None:
            tags = []
        self._tags = tags

    def has_tag(self, tag: Tag) -> bool:
        """return true if the tag key and value already exist in the model
        """
        return tag in self._tags

    def get_tag(self, key: str, value: TagValueType) -> Optional[Tag]:
        """return the tag if it exists
        """
        tags = [tag for tag in self._tags if tag.key == key and tag.value == value]

        if len(tags) > 0:
            return tags[0]

        return None

    def get_by_key(self, tag_key: str) -> List[Tag]:
        """return the tag if it exists
        """
        tags = [tag for tag in self._tags if tag.key == tag_key]

        return tags

    def get_first_by_key(self, tag_key: str) -> Optional[Tag]:
        """return the first tag with the given key or None if it does not exist
        """
        tags = self.get_by_key(tag_key)

        if len(tags) > 0:
            return tags[0]

        return None

    def has_tag_key(self, tag_key: str) -> bool:
        """return true if the tag key already exist in the model
        """
        return len(self.get_by_key(tag_key)) > 0

    def get_tags(self) -> List[Tag]:
        return self._tags

    def add_tag(self, tag: Tag) -> None:
        """Add a tag to the list if it does not exist
        """
        if not tag or not isinstance(tag, Tag):
            raise Exception("tag is not a Tag object")

        if not self.has_tag(tag):
            self._tags.append(tag)

    def add_tags(self, tags: List[Tag]) -> None:
        """Add a list of tags to the list if it does not exist
        """
        for tag in tags:
            self.add_tag(tag)

    def remove_loaded_tags(self) -> None:
        """Remove tags that are loaded from the database
        """
        self._tags = [tag for tag in self._tags if not tag.__is_field_loaded__]

    def count(self) -> int:
        """Return the number of tags
        """
        return len(self._tags)

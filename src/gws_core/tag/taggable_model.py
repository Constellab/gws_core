

from typing import Dict, List, Optional

from peewee import CharField
from peewee import Model as PeeweeModel

from .tag import Tag, TagHelper


class TaggableModel(PeeweeModel):
    """
    Class to extend to make the model support tags.
    """
    tags = CharField(null=True)

    def add_or_replace_tag(self, tag_key: str, tag_value: str) -> None:
        self.tags = TagHelper.add_or_replace_tag(self.tags, tag_key, tag_value)

    def get_tags(self) -> List[Tag]:
        return TagHelper.tags_to_list(self.tags)

    def set_tags(self, tags: List[Tag]) -> None:
        self.tags = TagHelper.tags_to_str(tags)

    def get_tag_value(self, tag_key: str) -> Optional[str]:
        tags = [x for x in self.get_tags() if x.key == tag_key]
        if len(tags) > 0:
            return tags[0].value

        return None

    def get_tags_json(self) -> List[Dict]:
        list_ = []
        for tag in self.get_tags():
            list_.append(tag.to_json())

        return list_

    def has_tag(self, tag: Tag) -> bool:
        """return true if the tag key and value already exist in the model
        """
        return tag in self.get_tags()

    ################################### SPECIAL TAGS ############################

    def set_name_tag(self, name: str) -> None:
        self.add_or_replace_tag("name", name)

    def get_name_tag(self) -> Optional[str]:
        return self.get_tag_value("name")

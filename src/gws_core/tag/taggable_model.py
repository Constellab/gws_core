# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Dict, List, Optional

from peewee import CharField, Expression
from peewee import Model as PeeweeModel

from gws_core.core.classes.expression_builder import ExpressionBuilder

from .tag import KEY_VALUE_SEPARATOR, TAGS_SEPARATOR, Tag
from .tag_helper import TagHelper


class TaggableModel(PeeweeModel):
    """
    Class to extend to make the model support tags.
    """
    tags = CharField(null=True, max_length=255)

    def add_or_replace_tag(self, tag_key: str, tag_value: str) -> None:
        self.tags = TagHelper.add_or_replace_tag(self.tags, tag_key, tag_value)

    def remove_tag(self, tag_key: str, tag_value: str) -> None:
        """remove the tag from the model
        """
        self.tags = TagHelper.remove_tag(self.tags, tag_key, tag_value)

    def get_tags(self) -> List[Tag]:
        return TagHelper.tags_to_list(self.tags)

    def set_tags(self, tags: List[Tag]) -> None:
        self.tags = TagHelper.tags_to_str(tags)

    def set_tags_dict(self, tags: Dict[str, str]) -> None:
        tags_list = TagHelper.tags_dict_to_list(tags)
        self.set_tags(tags_list)

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

    def has_tag_key(self, tag_key: str) -> bool:
        """return true if the tag key already exist in the model
        """
        return any(tag.key == tag_key for tag in self.get_tags())

    @classmethod
    def find_by_tags(cls, tags: List[Tag]) -> List["TaggableModel"]:
        """return a list of model that have the tag
        """
        return list(cls.select().where(cls.get_search_tag_expression(tags)))

    @classmethod
    def get_search_tag_expression(cls, tags: List[Tag]) -> Expression:
        """Get the filter expresion for a search in tags column
        """
        query_builder: ExpressionBuilder = ExpressionBuilder()
        for tag in tags:

            str_search = None
            if tag.value:
                str_search = TAGS_SEPARATOR + str(tag) + TAGS_SEPARATOR
            else:
                # if there is no value we return all the models that have the tag with the key
                str_search = TAGS_SEPARATOR + tag.key + KEY_VALUE_SEPARATOR

            # use a contains with ',' around to match exacty the tag key/value
            query_builder.add_expression(cls.tags.contains(str_search))
        return query_builder.build()

    @classmethod
    def get_tag_valie_start_with_expression(cls, tags: List[Tag]) -> Expression:
        """Get the filter expresion for a search in tags column
        """
        query_builder: ExpressionBuilder = ExpressionBuilder()
        for tag in tags:
            if not tag.value:
                raise Exception("The tag value must be set")

            # use a contains with ',' around to match exacty the tag key/value
            query_builder.add_expression(cls.tags.contains(TAGS_SEPARATOR + str(tag)))
        return query_builder.build()

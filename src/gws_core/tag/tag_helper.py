# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, List

from numpy import array, meshgrid
from peewee import CharField, Expression

from ..core.classes.expression_builder import ExpressionBuilder
from .tag import TAGS_SEPARATOR, Tag


class TagHelper():

    @classmethod
    def add_or_replace_tag(cls, tags_str: str, tag_key: str, tag_value: str) -> str:
        """Add of replace a tag key/value into a string
        """

        tags: List[Tag] = cls.tags_to_list(tags_str)

        if not tags:
            return str(Tag(tag_key, tag_value))

        same_key: List[Tag] = [x for x in tags if x.key == tag_key]

        if same_key:
            same_key[0].set_value(tag_value)
        else:
            tags.append(Tag(tag_key, tag_value))

        return cls.tags_to_str(tags)

    @classmethod
    def tags_to_str(cls, tags: List[Tag]) -> str:
        if not tags:
            return ''
        return TAGS_SEPARATOR.join([str(tag) for tag in tags])

    @classmethod
    def tags_to_list(cls, tags: str) -> List[Tag]:
        if not tags:
            return []

        tags_list: List[Tag] = []

        for tag_str in tags.split(TAGS_SEPARATOR):
            tags_list.append(Tag.from_string(tag_str))
        return tags_list

    @classmethod
    def tags_dict_to_list(cls, tags: Dict[str, str]) -> List[Tag]:
        if not tags:
            return []

        tags_list: List[Tag] = []

        for tag_key, tag_value in tags.items():
            tags_list.append(Tag(tag_key, tag_value))
        return tags_list

    @classmethod
    def get_search_tag_expression(cls, tag_str: str, tag_field: CharField) -> Expression:
        """ Get the filter expresion for a search in tags column

        :param filter_: [description]
        :type filter_: SearchFilterCriteria
        :return: [description]
        :rtype: Expression
        """
        tags: List[Tag] = cls.tags_to_list(tag_str)
        query_builder: ExpressionBuilder = ExpressionBuilder()
        for tag in tags:
            query_builder.add_expression(tag_field.contains(str(tag)))
        return query_builder.build()

    @classmethod
    def get_distinct_values(cls, tags: List[Dict[str, str]]) -> Dict[str, List[str]]:
        """Return a dictionary of tags key with the list of values for each key from a list of tags
        """
        all_tags = {}
        for tag in tags:
            for k, v in tag.items():
                if k not in all_tags:
                    all_tags[k] = []
                elif v in all_tags[k]:
                    continue
                all_tags[k].append(v)
        return all_tags

    @classmethod
    def get_all_tags_combinasons(cls, distinct_tags: Dict[str, List[str]]) -> List[Dict[str, str]]:
        """Return a list of all possible combinations of tags
        """
        tag_values = [v for v in distinct_tags.values()]

        # 2D array where each element in a array representing a combination
        result = array(meshgrid(*tag_values)).T.reshape(-1, len(tag_values))

        result_2 = []

        tag_keys = list(distinct_tags.keys())

        # loop over all combinations to retrieve key for each value
        for combination in result:
            tag_combinasion = {}
            i = 0
            for value in combination:
                tag_combinasion[tag_keys[i]] = value
                i += 1
            result_2.append(tag_combinasion)
        return result_2
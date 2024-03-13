

from datetime import datetime
from typing import Dict, List

from numpy import array, meshgrid

from gws_core.core.utils.date_helper import DateHelper
from gws_core.tag.tag_dto import EntityTagValueFormat, TagDTO

from .tag import TAGS_SEPARATOR, Tag, TagValueType


class TagHelper():

    @classmethod
    def tags_to_json(cls, tags: List[Tag]) -> List[dict]:
        if not tags:
            return []
        return [tag.to_dto().dict() for tag in tags]

    @classmethod
    def tags_to_list(cls, tags: str) -> List[Tag]:
        if not tags:
            return []

        tags_list: List[Tag] = []

        for tag_str in tags.split(TAGS_SEPARATOR):
            # skip the empty tag (like first and la separator)
            if len(tag_str) > 0:
                tags_list.append(Tag.from_string(tag_str))
        return tags_list

    @classmethod
    def tags_dict_to_list(cls, tags_dict: List[dict]) -> List[Tag]:
        if not tags_dict:
            return []

        tags_list: List[Tag] = []

        for tag_dict in tags_dict:
            tags_list.append(Tag.from_dto(TagDTO.from_json(tag_dict)))
        return tags_list

    @classmethod
    def tags_dict_to_list_v2(cls, tags_dict: List[TagDTO]) -> List[Tag]:
        if not tags_dict:
            return []

        tags_list: List[Tag] = []

        for tag_dict in tags_dict:
            tags_list.append(Tag.from_dto(tag_dict))
        return tags_list

    @classmethod
    def get_distinct_values(cls, tags: List[Dict[str, str]]) -> Dict[str, List[str]]:
        """Return a dictionary of tags key with the list of values for each key from a list of tags
        """
        all_tags: Dict[str, List[str]] = {}
        for tag in tags:
            for k, v in tag.items():
                if k not in all_tags:
                    all_tags[k] = []
                elif v in all_tags[k]:
                    continue
                all_tags[k].append(v)
        return all_tags

    @classmethod
    def get_distinct_values_for_key(cls, tags: List[Dict[str, str]], key: str) -> List[str]:
        """Return a list of distinct values for a key from a list of tags
        """
        distinct_tags = cls.get_distinct_values(tags)
        return distinct_tags.get(key, [])

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

    ################################ Tag value check ################################

    @classmethod
    def check_and_convert_value(cls, value: TagValueType, value_format: EntityTagValueFormat) -> TagValueType:
        if value is None:
            raise Exception("The tag value cannot be None")
        try:
            if cls._check_value(value, value_format):
                return value

            return cls.convert_str_value_to_type(value, value_format)
        except:
            raise Exception(f"Invalid value {value}, expected type {value_format.value}")

    @classmethod
    def _check_value(cls, value: TagValueType, value_format: EntityTagValueFormat) -> bool:
        if value is None:
            return False
        if value_format == EntityTagValueFormat.INTEGER:
            return isinstance(value, int)
        elif value_format == EntityTagValueFormat.FLOAT:
            return isinstance(value, float)
        elif value_format == EntityTagValueFormat.DATETIME:
            return isinstance(value, datetime)
        else:
            return isinstance(value, str)

    @classmethod
    def convert_str_value_to_type(cls, value: str, value_format: EntityTagValueFormat) -> TagValueType:
        if value_format == EntityTagValueFormat.INTEGER:
            return int(value)
        elif value_format == EntityTagValueFormat.FLOAT:
            return float(value)
        elif value_format == EntityTagValueFormat.DATETIME:
            return DateHelper.from_iso_str(value)
        else:
            return value

    @classmethod
    def convert_value_to_str(cls, value: TagValueType) -> str:
        if isinstance(value, datetime):
            return DateHelper.to_iso_str(value)
        else:
            return str(value)

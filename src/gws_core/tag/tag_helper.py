from datetime import datetime

from numpy import array, meshgrid

from gws_core.tag.tag_dto import TagDTO, TagValueFormat

from .tag import Tag, TagValueType


class TagHelper:
    @classmethod
    def tags_to_json(cls, tags: list[Tag]) -> list[dict]:
        if not tags:
            return []
        return [tag.to_dto().to_json_dict() for tag in tags]

    @classmethod
    def tags_dict_to_list(cls, tags_dict: list[dict]) -> list[Tag]:
        if not tags_dict:
            return []

        tags_list: list[Tag] = []

        for tag_dict in tags_dict:
            tags_list.append(Tag.from_dto(TagDTO.from_json(tag_dict)))
        return tags_list

    @classmethod
    def tags_dto_to_list(cls, tags_dict: list[TagDTO]) -> list[Tag]:
        if not tags_dict:
            return []

        tags_list: list[Tag] = []

        for tag_dict in tags_dict:
            tags_list.append(Tag.from_dto(tag_dict))
        return tags_list

    @classmethod
    def get_distinct_values(cls, tags: list[dict[str, str]]) -> dict[str, list[str]]:
        """Return a dictionary of tags key with the list of values for each key from a list of tags"""
        all_tags: dict[str, list[str]] = {}
        for tag in tags:
            for k, v in tag.items():
                if k not in all_tags:
                    all_tags[k] = []
                elif v in all_tags[k]:
                    continue
                all_tags[k].append(v)
        return all_tags

    @classmethod
    def get_distinct_values_for_key(cls, tags: list[dict[str, str]], key: str) -> list[str]:
        """Return a list of distinct values for a key from a list of tags"""
        distinct_tags = cls.get_distinct_values(tags)
        return distinct_tags.get(key, [])

    @classmethod
    def get_all_tags_combinasons(cls, distinct_tags: dict[str, list[str]]) -> list[dict[str, str]]:
        """Return a list of all possible combinations of tags"""
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
    def check_and_convert_value(
        cls, value: TagValueType, value_format: TagValueFormat
    ) -> TagValueType:
        if value is None:
            raise Exception("The tag value cannot be None")
        try:
            if cls._check_value(value, value_format):
                return value

            return cls.convert_str_value_to_type(value, value_format)
        except:
            raise Exception(f"Invalid value {value}, expected type {value_format.value}")

    @classmethod
    def _check_value(cls, value: TagValueType, value_format: TagValueFormat) -> bool:
        if value is None:
            return False
        if value_format == TagValueFormat.INTEGER:
            return isinstance(value, int)
        elif value_format == TagValueFormat.FLOAT:
            return isinstance(value, float)
        elif value_format == TagValueFormat.DATETIME:
            return isinstance(value, datetime)
        else:
            return isinstance(value, str)

    @classmethod
    def convert_str_value_to_type(cls, value: str, value_format: TagValueFormat) -> TagValueType:
        return Tag.convert_str_value_to_type(value, value_format)

    @classmethod
    def convert_value_to_str(cls, value: TagValueType) -> str:
        return Tag.convert_value_to_str(value)

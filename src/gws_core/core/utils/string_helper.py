# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import random
import re
import string
import uuid
from typing import Any, Type

from slugify import slugify as _slugify


class StringHelper():
    """Helper to manipulate strings
    """

    @staticmethod
    def generate_random_chars(size=6, chars=string.ascii_uppercase + string.ascii_lowercase + string.digits) -> str:
        return ''.join(random.choice(chars) for _ in range(size))

    @classmethod
    def generate_uuid(cls) -> str:
        return str(uuid.uuid4())

    @staticmethod
    def slugify(text: str, snakefy: bool = False, to_lower: bool = True) -> str:
        """
        Returns the slugified text

        :param text: Text to slugify
        :type text: `str`
        :param snakefy: Snakefy the text if True (i.e. uses undescores instead of dashes to separate text words), defaults to False
        :type snakefy: `bool`
        :param to_lower: True to lower all characters, False otherwise
        :type to_lower: `bool`
        :return: The slugified text
        :rtype: str
        """

        if snakefy:
            text = _slugify(text, to_lower=to_lower, separator="_")
        else:
            text = _slugify(text, to_lower=to_lower, separator='-')

        return text

    @staticmethod
    def camel_case_to_sentence(name: str) -> str:
        """Convert a camel case to sentence like
        Ex 'TestClass2Build' -> 'Test class2 build'

        :param name: [description]
        :type name: str
        :return: [description]
        :rtype: str
        """
        if name is None:
            return None
        name = name.replace(' ', '')
        name = re.sub('(.)([A-Z][a-z]+)', r'\1 \2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1 \2', name).capitalize()

    @staticmethod
    def snake_case_to_sentence(name: str) -> str:
        """Convert a snake case to sentence like
        Ex 'test_class2_build' -> 'Test class2 build'
        """
        if name is None:
            return None
        name = name.lower().replace(' ', '').replace('_', ' ')
        return name.capitalize()

    @staticmethod
    def to_enum(enum_class: Type, str_value: str) -> Any:
        """Convert a string to an enum value
        """
        return enum_class(str_value)

    @staticmethod
    def is_alphanumeric(str_: str) -> bool:
        """Check if a string is alphanumeric with underscore"""
        if str_ is None:
            return False

        return bool(re.match("^[a-zA-Z0-9_]+$", str_))

    @staticmethod
    def remove_whitespaces(str_: str) -> str:
        """Remove all whitespace of a string"""
        if str_ is None:
            return None

        pattern = re.compile(r'\s+')
        return re.sub(pattern, '', str_)

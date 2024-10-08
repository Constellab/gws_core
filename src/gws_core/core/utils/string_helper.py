

import random
import re
import string
import uuid
from typing import Any, Type

from slugify import slugify as _slugify
from unidecode import unidecode


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
            text = _slugify(text, lowercase=to_lower, separator="_")
        else:
            text = _slugify(text, lowercase=to_lower, separator='-')

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
    def to_pascal_case(text: str) -> str:
        """Convert a text to pascal case
        Ex 'test_class2_build' -> 'TestClass2Build'
        """
        if text is None:
            return None
        # Split the input string into words based on spaces or underscores
        words = re.split(r'[ _]', text)

        # Capitalize the first letter of each word and join them
        pascal_case_string = ''.join(word.capitalize() for word in words if word)

        return pascal_case_string

    @staticmethod
    def to_snake_case(text: str) -> str:
        """Convert a text to snake case
        Ex 'TestClass2Build' -> 'test_class2_build'
        """
        if text is None:
            return None

        # Replace spaces or hyphens with underscores
        text = re.sub(r'[\s\-]+', '_', text)

        # Insert underscores before uppercase letters (except the first one)
        text = re.sub(r'(?<!^)(?=[A-Z])', '_', text)

        # Convert the entire string to lowercase
        text = text.lower()

        # Remove double (or more) underscores
        text = re.sub(r'_{2,}', '_', text)

        return text

    @staticmethod
    def to_enum(enum_class: Type, str_value: str) -> Any:
        """Convert a string to an enum value
        """
        return enum_class(str_value)

    @staticmethod
    def get_enum_values(enum_class: Type) -> list:
        """Get all the values of an enum
        """
        return [e.value for e in enum_class]

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

    @staticmethod
    def replace_accent_with_letter(str_: str) -> str:
        """Replace accent with letter"""
        if str_ is None:
            return None

        return unidecode(str_)

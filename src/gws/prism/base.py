# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from slugify import slugify as convert_to_slug
import inspect
import re

class Base:

    def classname(self, slugify = False, snakefy = False, separate_upper = False) -> str:
        name = type(self).__name__
        if separate_upper:
            name = re.sub('([A-Z]{1})', r'-\1', name)
            name = name.strip("-")

        if slugify:
            name = convert_to_slug(name, to_lower=True, separator='-')
        elif snakefy:
            name = convert_to_slug(name, to_lower=True, separator='_')
        return name
    
    @classmethod
    def full_classname(cls, slugify = False, snakefy = False):
        module = inspect.getmodule(cls).__name__
        name = cls.__name__
        full_name = module + "." + name

        if slugify:
            full_name = convert_to_slug(full_name, to_lower=True, separator='-')
        elif snakefy:
            full_name = convert_to_slug(full_name, to_lower=True, separator='_')
        
        return full_name

    @classmethod
    def module(cls):
        module = inspect.getmodule(cls).__name__
        return module

    @property
    def property_names(self):
        property_names = [p for p in dir(self) if isinstance(getattr(self,p),property)]
        return property_names
    
    @property
    def method_names(self):
        property_names = [p for p in dir(self) if not isinstance(getattr(self,p),property)]
        return property_names


def slugify(name, snakefy = False) -> str:
    if slugify:
        name = convert_to_slug(name, to_lower=True, separator='-')
    elif snakefy:
        name = convert_to_slug(name, to_lower=True, separator='_')
    return name
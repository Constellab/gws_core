#
# Python GWS view
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
#

from slugify import slugify as convert_to_slug

class Base:

    def classname(self, slugify = False, snakefy = False, full=False) -> str:
        name = type(self).__name__

        if full:
            module = self.__class__.__module__
            if module is None or module == str.__class__.__module__:
                return self.__class__.__name__  # Avoid reporting __builtin__
            else:
                return module + '.' + self.__class__.__name__
        else:
            if slugify:
                name = convert_to_slug(name, to_lower=True, separator='-')
            elif snakefy:
                name = convert_to_slug(name, to_lower=True, separator='_')
            
        return name
    
    @property
    def property_names(self):
        property_names = [p for p in dir(self) if isinstance(getattr(self,p),property)]
        return property_names
    
    @property
    def method_names(self):
        property_names = [p for p in dir(self) if not isinstance(getattr(self,p),property)]
        return property_names
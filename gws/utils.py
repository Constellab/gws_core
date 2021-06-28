# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import string
import random
from slugify import slugify as _slugify

# -- G --

def generate_random_chars(size=6, chars=string.ascii_uppercase + string.ascii_lowercase + string.digits) -> str:
    return ''.join(random.choice(chars) for _ in range(size))
    
    
# -- S --

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

# -- S --

def sort_dict_by_key(d):
    if not d:
        return d
    
    return {k: sort_dict_by_key(v) if isinstance(v, dict) else v
            for k, v in sorted(d.items())}

# -- T --

def to_camel_case(snake_str: str, capitalize_first:bool = False):
    components = snake_str.split('_')
    c0 = components[0].title() if capitalize_first else components[0]
    return c0 + ''.join(x.title() for x in components[1:])

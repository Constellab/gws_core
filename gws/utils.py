# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import string
import random

from slugify import slugify as _slugify

def slugify(text: str, snakefy: bool = False) -> str:
    """
    Returns the slugified text

    :param snakefy: Snakefy the text if True (i.e. uses undescores instead of dashes to separate text words), defaults to False
    :type snakefy: bool, optional
    :return: The slugified name
    :rtype: str
    """
    
    if snakefy:
        text = _slugify(text, to_lower=True, separator='_')
    else:
        text = _slugify(text, to_lower=True, separator='-')
        
    return text

def generate_random_chars(size=6, chars=string.ascii_uppercase + string.ascii_lowercase + string.digits) -> str:
    return ''.join(random.choice(chars) for _ in range(size))
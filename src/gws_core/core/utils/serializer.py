# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any
import dill

class Serializer:
    """Serializer"""

    @staticmethod
    def dump(obj, path: str, *args, **kwargs):
        """Dump an object into a file"""

        with open(path, "wb") as fp:
            dill.dump(obj, fp)

    @staticmethod
    def load(path: str, *args, **kwargs) -> Any:
        """Load an object from a file"""

        with open(path, "rb") as fp:
            return dill.load(fp)
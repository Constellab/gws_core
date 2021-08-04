# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import inspect
from typing import List

from peewee import CharField

from ..core.model.model import Model
from .viewable import Viewable

# ####################################################################
#
# ProcessType class
#
# ####################################################################


class Typing(Viewable):
    """
    Typing class. This class allows storing information on all the types of the models in the system.

    :property type: The type of the related model.
    :type type: `str`
    :property super_type: The super type of the related model.
    :type super_type: `str`
    :property root_type: The root type of the related process.
    :type root_type: `str`
    """

    model_type: str = CharField(null=True, index=True, unique=True)
    root_model_type: str = CharField(null=True, index=True)
    #ancestors = TextField(null=True)

    _table_name = 'gws_typing'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.data.get("ancestors"):
            self.data["ancestors"] = self.__get_hierarchy_table()

    # -- G --

    def get_model_types_array(self) -> List[str]:
        """
        Return the model_type as an array by splitting with .
        """

        return self.model_type.split('.')

    def __get_hierarchy_table(self) -> List[str]:
        model_t: Model = self.get_model_type(self.model_type)
        mro: List[Model] = inspect.getmro(model_t)

        ht: List[str] = []
        for t in mro:
            if issubclass(t, Model):
                ht.append(t.full_classname())

        return ht

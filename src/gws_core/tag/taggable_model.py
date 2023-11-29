# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from peewee import CharField
from peewee import Model as PeeweeModel


class TaggableModel(PeeweeModel):
    """
    Class to extend to make the model support tags.
    Deprecated
    """
    tags = CharField(null=True, max_length=255)

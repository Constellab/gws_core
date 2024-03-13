

from peewee import CharField
from peewee import Model as PeeweeModel


class TaggableModel(PeeweeModel):
    """
    Class to extend to make the model support tags.
    Deprecated
    """
    tags = CharField(null=True, max_length=255)

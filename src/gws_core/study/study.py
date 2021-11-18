# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from peewee import CharField, ForeignKeyField

from ..core.model.model import Model
from ..model.typing_register_decorator import typing_registrator
from ..user.user import User


@typing_registrator(unique_name="Study", object_type="MODEL", hide=True)
class Study(Model):
    """
    Study class.
    """
    title: str = CharField(null=False)
    description: str = CharField(null=False)
    owner: User = ForeignKeyField(User, null=False)

    _table_name = 'gws_study'

    def archive(self, archive: bool) -> 'Study':
        """
        Deactivated method.
        """

        return None

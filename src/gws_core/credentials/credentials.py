# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Optional, final

from peewee import CharField, ModelSelect, TextField

from gws_core.core.classes.enum_field import EnumField
from gws_core.core.model.model_with_user import ModelWithUser

from .credentials_type import CredentialsType


@final
class Credentials(ModelWithUser):

    name = CharField(max_length=255, null=False, unique=True)
    type: CredentialsType = EnumField(choices=CredentialsType)

    description = TextField(null=True)

    _table_name = "gws_credentials"

    def data_to_json(self, deep: bool = False, **kwargs) -> dict:
        return None

    @classmethod
    def find_by_name(cls, name: str) -> Optional['Credentials']:
        return cls.select().where(Credentials.name == name).first()

    @classmethod
    def search_by_name(cls, name: str) -> ModelSelect:
        return cls.select().where(Credentials.name.contains(name))

    @classmethod
    def search_by_name_and_type(cls, name: str, type_: CredentialsType) -> ModelSelect:
        if not name:
            return cls.select().where(Credentials.type == type_)
        return cls.select().where(Credentials.name.contains(name), Credentials.type == type_)



from typing import Any, Dict, Optional, final

from peewee import CharField, ModelSelect, TextField

from gws_core.core.classes.enum_field import EnumField
from gws_core.core.model.db_field import JSONField
from gws_core.core.model.model_with_user import ModelWithUser
from gws_core.credentials.credentials_dto import CredentialDTO

from .credentials_type import CredentialsType


@final
class Credentials(ModelWithUser):

    name = CharField(max_length=255, null=False, unique=True)
    type: CredentialsType = EnumField(choices=CredentialsType)

    description = TextField(null=True)

    data: Dict[str, Any] = JSONField(null=True)

    _table_name = "gws_credentials"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_saved() and not self.data:
            self.data = {}

    def to_dto(self) -> CredentialDTO:
        return CredentialDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            created_by=self.created_by.to_dto(),
            last_modified_by=self.last_modified_by.to_dto(),
            name=self.name,
            type=self.type,
            description=self.description,
        )

    @classmethod
    def find_by_name(cls, name: str) -> Optional['Credentials']:
        return cls.select().where(Credentials.name == name).first()

    @classmethod
    def search_by_type(cls, type_: CredentialsType) -> ModelSelect:
        return cls.select().where(Credentials.type == type_)

    @classmethod
    def search_by_name(cls, name: str) -> ModelSelect:
        return cls.select().where(Credentials.name.contains(name))

    @classmethod
    def search_by_name_and_type(cls, name: str, type_: CredentialsType) -> ModelSelect:
        if not name:
            return cls.select().where(Credentials.type == type_)
        return cls.select().where(Credentials.name.contains(name), Credentials.type == type_)

    class Meta:
        table_name = "gws_credentials"

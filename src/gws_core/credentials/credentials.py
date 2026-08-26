import builtins
from typing import Optional, final

from peewee import ModelSelect

from gws_core.core.model.model_with_user import ModelWithUser
from gws_core.core.model.typed_db_field import (
    NullableJSONField,
    NullableTextField,
    TypedCharField,
)
from gws_core.credentials.credentials_registry import CredentialsRegistry
from gws_core.credentials.credentials_type import CredentialsDTO, CredentialsTypeDTO

from .credentials_type import (
    CredentialsDataBase,
)


@final
class Credentials(ModelWithUser):
    name: TypedCharField = TypedCharField(max_length=255, unique=True)
    type: TypedCharField = TypedCharField(max_length=255)

    description: NullableTextField = NullableTextField()

    data: NullableJSONField = NullableJSONField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_saved() and not self.data:
            self.data = {}

    def to_dto(self) -> CredentialsDTO:
        return CredentialsDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            created_by=self.created_by.to_dto(),
            last_modified_by=self.last_modified_by.to_dto(),
            name=self.name,
            type=self._get_type_dto(),
            description=self.description,
        )

    def _get_type_dto(self) -> CredentialsTypeDTO:
        """Build the type metadata DTO from the stored type id. Falls back to a
        minimal DTO when the id is not (or no longer) registered, e.g. the owning
        brick is disabled."""
        data_type = CredentialsRegistry.get_data_type(self.type)
        if data_type is not None:
            return data_type.get_type_dto()

        brick_name = self.type.split(".")[0] if "." in self.type else ""
        return CredentialsTypeDTO(type=self.type, brick_name=brick_name, human_name=self.type)

    def get_credentials_data_type(self) -> builtins.type[CredentialsDataBase]:
        return CredentialsRegistry.get_and_check_data_type(self.type)

    def get_data_object(self) -> CredentialsDataBase:
        data_type = self.get_credentials_data_type()
        return data_type.build_from_json(self.data or {}, self.to_dto())

    @classmethod
    def find_by_name(cls, name: str) -> Optional["Credentials"]:
        return cls.select().where(Credentials.name == name).first()

    @classmethod
    def find_by_name_and_check(cls, name: str, type_: str | None = None) -> "Credentials":
        credentials = cls.find_by_name(name)
        if not credentials:
            raise Exception(
                f"Credentials '{name}' not found, does it exist or was it renamed or deleted?"
            )

        if type_ is not None and credentials.type != type_:
            raise Exception(
                f"Credentials {name} does ont have the correct type. Expected type : '{type_}', found type : '{credentials.type}'. Was the credentials '{name}' updated?"
            )
        return credentials

    @classmethod
    def search_by_type(cls, type_: str) -> ModelSelect:
        return cls.select().where(Credentials.type == type_)

    @classmethod
    def search_by_types(cls, types: list[str]) -> ModelSelect:
        return cls.select().where(Credentials.type.in_(types))

    @classmethod
    def search_by_name(cls, name: str) -> ModelSelect:
        return cls.select().where(Credentials.name.contains(name))

    @classmethod
    def search_by_name_and_type(cls, name: str, type_: str) -> ModelSelect:
        if not name:
            return cls.select().where(Credentials.type == type_)
        return cls.select().where(Credentials.name.contains(name), Credentials.type == type_)

    class Meta:
        table_name = "gws_credentials"
        is_table = True
